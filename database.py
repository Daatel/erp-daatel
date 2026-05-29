import sqlite3
import pandas as pd
import os
import streamlit as st
import hashlib
import secrets

DB_NAME = "erp_fabrica.db"

def hash_password(password: str) -> str:
    if not password:
        return ""
    salt = secrets.token_hex(8)
    hash_val = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"sha256${salt}${hash_val}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    if not stored_password or not provided_password:
        return False
    if not stored_password.startswith("sha256$"):
        # Retrocompatibilidade com senhas antigas em texto plano
        return stored_password == provided_password
    try:
        parts = stored_password.split("$")
        if len(parts) != 3:
            return False
        algo, salt, hash_val = parts
        calc_hash = hashlib.sha256((provided_password + salt).encode('utf-8')).hexdigest()
        return secrets.compare_digest(hash_val, calc_hash)
    except Exception:
        return False


@st.cache_resource
def init_connection_pool():
    if "DATABASE_URL" in st.secrets:
        from psycopg2 import pool
        # Pool thread-safe com até 20 conexões reaproveitáveis
        return pool.ThreadedConnectionPool(1, 20, st.secrets["DATABASE_URL"])
    return None

def get_connection():
    pool = init_connection_pool()
    if pool:
        return pool.getconn()
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def release_connection(conn):
    pool = init_connection_pool()
    if pool and hasattr(conn, 'info'): # é psycopg2
        pool.putconn(conn)
    elif not pool:
        conn.close()

from contextlib import contextmanager

@contextmanager
def db_connection():
    """Context manager que garante devolução da conexão ao pool mesmo em caso de exceção."""
    conn = get_connection()
    try:
        yield conn
    finally:
        release_connection(conn)

def format_pg(sql):
    if "DATABASE_URL" in st.secrets:
        import re
        sql = re.sub(r"(?i)\bas\s+'([^']+)'", r'as "\1"', sql)
        sql = sql.replace("%", "%%")
        sql = sql.replace("?", "%s")
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        sql = sql.replace("DATETIME DEFAULT CURRENT_TIMESTAMP", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        sql = sql.replace("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")
        sql = sql.replace("BOOLEAN DEFAULT 1", "BOOLEAN DEFAULT TRUE")
        
        # Tornar ALTER TABLE ADD COLUMN idempotente no PostgreSQL (adiciona IF NOT EXISTS)
        sql = re.sub(
            r'(?i)(ALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN\s+)(?!IF\s+NOT\s+EXISTS\s+)',
            r'\1IF NOT EXISTS ',
            sql
        )
        
        # Remove FOREIGN KEY para evitar erro de ordem (relação não existe)
        linhas = []
        for linha in sql.split('\n'):
            if "FOREIGN KEY" not in linha.upper():
                linhas.append(linha)
        sql = '\n'.join(linhas)
        sql = re.sub(r",\s*\)", "\n    )", sql)
    else:
        # SQLite: traduz string_agg do PostgreSQL para group_concat do SQLite
        sql = sql.replace("string_agg", "group_concat")
    return sql

class CursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
    def execute(self, sql, *args):
        self.cursor.execute(format_pg(sql), *args)
    def fetchone(self):
        return self.cursor.fetchone()

def create_tables():
    conn = get_connection()
    try:
        _create_tables_internal(conn)
    finally:
        release_connection(conn)

@st.cache_resource
def initialize_database():
    create_tables()
    return True

def _create_tables_internal(conn):
    cursor = CursorWrapper(conn.cursor())

    # 0. Redes de Clientes e Grupos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS redes_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grupos_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rede_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        FOREIGN KEY(rede_id) REFERENCES redes_clientes(id)
    )
    ''')

    # 1. Produtos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        unidade_medida TEXT NOT NULL,
        preco_venda_base REAL DEFAULT 0.0,
        is_materia_prima BOOLEAN DEFAULT 0,
        marca TEXT,
        peso_volume TEXT,
        referencia TEXT,
        ean TEXT,
        unidades_por_fardo INTEGER,
        tipo_embalagem TEXT,
        custo_unidade REAL DEFAULT 0.0,
        custo_fardo REAL DEFAULT 0.0,
        estoque_minimo REAL DEFAULT 0.0
    )
    ''')

    # 4. Funcionarios (RH)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cargo TEXT NOT NULL,
        salario_base REAL NOT NULL,
        regime_contratacao TEXT, 
        data_admissao DATE,
        dia_vencimento_comissao INTEGER DEFAULT 31,
        gatilho_comissao TEXT DEFAULT 'FATURAMENTO',
        data_nascimento DATE,
        ajuda_custo REAL DEFAULT 0.0,
        outros_descricao TEXT,
        outros_valor REAL DEFAULT 0.0,
        status TEXT DEFAULT 'ATIVO',
        data_termino DATE
    )
    ''')

    # 2. Clientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT,
        endereco TEXT,
        nome_fantasia TEXT,
        cnpj_cpf TEXT,
        inscricao_estadual TEXT,
        bairro TEXT,
        cep TEXT,
        cidade TEXT,
        uf TEXT,
        email TEXT,
        observacoes TEXT,
        status TEXT,
        rede_clientes TEXT,
        grupo_lojas TEXT,
        prazo_pagamento TEXT,
        prazo_pagamento_dias INTEGER DEFAULT 30,
        representante_id INTEGER,
        data_nascimento DATE,
        FOREIGN KEY(representante_id) REFERENCES funcionarios(id)
    )
    ''')

    # 3. Fornecedores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT,
        cnpj_cpf TEXT,
        nome_fantasia TEXT,
        inscricao_estadual TEXT,
        endereco TEXT,
        bairro TEXT,
        cep TEXT,
        cidade TEXT,
        uf TEXT,
        email TEXT,
        plano_de_contas TEXT,
        status TEXT,
        prazo_pagamento TEXT
    )
    ''')
    
    # 5. Regras de Comissão
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comissoes_regras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor_id INTEGER,
        produto_id INTEGER,
        rede_clientes TEXT,
        percentual REAL NOT NULL,
        gatilho_comissao TEXT,
        minimo_garantido INTEGER DEFAULT 0,
        valor_minimo_garantido REAL DEFAULT 0.0,
        FOREIGN KEY(vendedor_id) REFERENCES funcionarios(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # 6. RH Pagamentos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rh_pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funcionario_id INTEGER,
        data_pagamento DATE,
        mes_referencia TEXT,
        salario_base_pago REAL,
        passagem REAL DEFAULT 0.0,
        refeicao REAL DEFAULT 0.0,
        custo_previdenciario REAL DEFAULT 0.0,
        valor_total_pago REAL,
        FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id)
    )
    ''')

    # 7. Compras de Matéria Prima
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compras_materia_prima (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATE,
        fornecedor_id INTEGER,
        peso_kg REAL,
        preco_unitario REAL,
        valor_total REAL,
        FOREIGN KEY(fornecedor_id) REFERENCES fornecedores(id)
    )
    ''')

    # 8. Produção Diária (Lotes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS producao_diaria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATE,
        hora_inicio TIME,
        hora_fim TIME,
        materia_prima_kg REAL,
        produto_id INTEGER,
        produto_final_kg REAL,
        perdas_kg REAL,
        observacoes TEXT,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # 8.1. Insumos Consumidos no Lote de Produção
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS producao_insumos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producao_id INTEGER,
        produto_id INTEGER,
        quantidade REAL,
        FOREIGN KEY(producao_id) REFERENCES producao_diaria(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # 9. Movimentos de Estoque
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS estoque_movimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATETIME DEFAULT CURRENT_TIMESTAMP,
        produto_id INTEGER,
        tipo_movimento TEXT, 
        quantidade REAL,
        origem TEXT, 
        plano_conta_id INTEGER,
        documento_referencia TEXT,
        lote_origem_id INTEGER,
        FOREIGN KEY(produto_id) REFERENCES produtos(id),
        FOREIGN KEY(plano_conta_id) REFERENCES planos_de_contas(id)
    )
    ''')

    # 10. Vendas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATE,
        cliente_id INTEGER,
        vendedor_id INTEGER,
        produto_id INTEGER,
        quantidade REAL,
        valor_unitario REAL,
        valor_total REAL,
        comissao_valor REAL,
        tipo_documento TEXT,
        numero_documento TEXT,
        manifesto_id INTEGER,
        custo_frete_rateado REAL DEFAULT 0.0,
        status TEXT DEFAULT 'APROVADO',
        comprovante_url TEXT,
        is_bonificacao BOOLEAN DEFAULT 0,
        custo_cmv_real REAL DEFAULT 0.0,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(vendedor_id) REFERENCES funcionarios(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id),
        FOREIGN KEY(manifesto_id) REFERENCES manifestos_carga(id)
    )
    ''')

    # 11. Fluxo de Caixa
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fluxo_caixa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATE,
        tipo TEXT,
        categoria TEXT,
        descricao TEXT,
        valor REAL,
        fonte_id INTEGER,
        conta_bancaria_id INTEGER,
        conciliado BOOLEAN DEFAULT 0,
        cliente_id INTEGER,
        FOREIGN KEY(conta_bancaria_id) REFERENCES contas_bancarias(id)
    )
    ''')

    # 12. Planos de Contas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS planos_de_contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        categoria TEXT NOT NULL,
        nome TEXT NOT NULL
    )
    ''')

    # 13. Compras (Matéria Prima, Insumos, Embalagens, etc)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fornecedor_id INTEGER NOT NULL,
        data_compra DATE NOT NULL,
        tipo_insumo TEXT NOT NULL,
        valor_total REAL NOT NULL,
        tipo_doc TEXT,
        numero_doc TEXT,
        observacoes TEXT,
        FOREIGN KEY(fornecedor_id) REFERENCES fornecedores(id)
    )
    ''')

    # 14. Contas a Pagar (Vinculadas às Compras ou Avulsas)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contas_a_pagar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compra_id INTEGER,
        fornecedor_id INTEGER,
        plano_conta_id INTEGER,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data_vencimento DATE NOT NULL,
        data_pagamento DATE,
        status TEXT NOT NULL DEFAULT 'PENDENTE',
        conta_bancaria_id INTEGER,
        cliente_id INTEGER,
        FOREIGN KEY(compra_id) REFERENCES compras(id),
        FOREIGN KEY(fornecedor_id) REFERENCES fornecedores(id),
        FOREIGN KEY(plano_conta_id) REFERENCES planos_de_contas(id),
        FOREIGN KEY(conta_bancaria_id) REFERENCES contas_bancarias(id)
    )
    ''')

    # 15. Contas Bancárias
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contas_bancarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        banco TEXT,
        agencia TEXT,
        conta TEXT,
        saldo_inicial REAL DEFAULT 0.0,
        tipo_conta TEXT,
        status TEXT DEFAULT 'ATIVO'
    )
    ''')

    # 16. Contas a Receber
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contas_a_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER,
        cliente_id INTEGER,
        plano_conta_id INTEGER,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data_vencimento DATE NOT NULL,
        data_recebimento DATE,
        status TEXT NOT NULL DEFAULT 'PENDENTE',
        conta_bancaria_id INTEGER,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(conta_bancaria_id) REFERENCES contas_bancarias(id)
    )
    ''')

    # 17. Maquinário e Ativos Fixos (Holding Imobilizada)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maquinario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        valor_aquisicao REAL DEFAULT 0.0,
        vida_util_anos REAL DEFAULT 0.0,
        valor_depreciacao_mensal REAL DEFAULT 0.0,
        data_aquisicao DATE,
        status TEXT DEFAULT 'ATIVO',
        observacoes TEXT
    )
    ''')

    # 18. Controle de Governança (Usuários ERP)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funcionario_id INTEGER UNIQUE,
        nome TEXT NOT NULL,
        email TEXT UNIQUE,
        senha TEXT NOT NULL,
        nivel_permissao TEXT NOT NULL,
        status TEXT DEFAULT 'ATIVO',
        FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id)
    )
    ''')
    
    # 19. Logística Reversa (Devoluções e Shelf Life)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devolucoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATE,
        cliente_id INTEGER,
        produto_id INTEGER,
        quantidade REAL,
        motivo TEXT,
        valor_financeiro_abatido REAL,
        observacoes TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # 20. Manifestos de Carga (Logística)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS manifestos_carga (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        data_saida DATE,
        placa_veiculo TEXT,
        motorista_nome TEXT,
        tipo_frete TEXT,
        valor_total_frete REAL DEFAULT 0.0,
        status TEXT DEFAULT 'EM TRÂNSITO',
        observacoes TEXT
    )
    ''')

    # 21. Itens de Compra (Linha de NF — Multi-Item)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compras_itens (
        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
        compra_id              INTEGER NOT NULL,
        produto_id             INTEGER,
        produto_nome           TEXT,
        destino                TEXT NOT NULL DEFAULT 'PRODUCAO',
        unidade                TEXT,
        quantidade             REAL NOT NULL,
        quantidade_estoque     REAL,
        preco_unitario_bruto   REAL NOT NULL,
        icms_valor             REAL DEFAULT 0.0,
        ipi_valor              REAL DEFAULT 0.0,
        custo_unitario_liquido REAL NOT NULL,
        total_liquido_item     REAL NOT NULL,
        FOREIGN KEY(compra_id)  REFERENCES compras(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # 22. Tabelas de Preços (Clientes, Redes ou Grupos)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tabelas_preco (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        tipo_entidade TEXT NOT NULL,
        entidade_nome TEXT NOT NULL,
        preco REAL NOT NULL,
        status TEXT DEFAULT 'ATIVO',
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # 23. Fichas Técnicas de Produção (BOM — Bill of Materials)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fichas_tecnicas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL UNIQUE,
        rendimento_percentual REAL DEFAULT 70.0,
        observacoes TEXT,
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )
    ''')

    # 24. Itens da Ficha Técnica (ingredientes / insumos da receita)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fichas_tecnicas_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ficha_id INTEGER NOT NULL,
        insumo_id INTEGER NOT NULL,
        quantidade_por_unidade REAL NOT NULL,
        tipo TEXT DEFAULT 'MP',
        FOREIGN KEY(ficha_id) REFERENCES fichas_tecnicas(id),
        FOREIGN KEY(insumo_id) REFERENCES produtos(id)
    )
    ''')

    # 25. Comodatos (Freezers e Equipamentos em Clientes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comodatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        maquina_id INTEGER NOT NULL,
        cliente_id INTEGER NOT NULL,
        data_inicio DATE NOT NULL,
        data_vencimento DATE NOT NULL,
        status TEXT DEFAULT 'ATIVO',
        contrato_gerado BOOLEAN DEFAULT 0,
        FOREIGN KEY(maquina_id) REFERENCES maquinario(id),
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
    ''')

    # 26. Dados da Empresa Adquirente (Dona do Sistema)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS empresa_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        razao_social TEXT NOT NULL,
        nome_fantasia TEXT,
        cnpj TEXT,
        endereco_completo TEXT,
        telefone TEXT,
        email TEXT,
        inscricao_estadual TEXT,
        inscricao_municipal TEXT,
        cep TEXT,
        instagram TEXT,
        website TEXT
    )
    ''')
    
    # Inserir empresa padrão se não existir
    cursor.execute("SELECT COUNT(*) FROM empresa_config")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO empresa_config (razao_social, nome_fantasia, cnpj, endereco_completo) VALUES ('Empório do Alho LTDA', 'Empório do Alho', '00.000.000/0001-00', 'Rua Principal, 123 - Centro')")

    conn.commit() # Salva as tabelas base antes das migrações de coluna

    # Migração: Adicionar colunas se não existirem
    alter_queries = [
        "ALTER TABLE compras_itens ADD COLUMN unidade TEXT",
        "ALTER TABLE compras_itens ADD COLUMN quantidade_estoque REAL",
        "ALTER TABLE compras_itens ADD COLUMN produto_nome TEXT",
        "ALTER TABLE produtos ADD COLUMN embalagem_master TEXT",
        "ALTER TABLE produtos ADD COLUMN cod_emb_master TEXT",
        "ALTER TABLE producao_diaria ADD COLUMN custo_total_lote REAL",
        "ALTER TABLE producao_diaria ADD COLUMN custo_unitario_lote REAL",
        "ALTER TABLE producao_diaria ADD COLUMN data_validade DATE",
        "ALTER TABLE vendas ADD COLUMN lote_impresso TEXT",
        "ALTER TABLE vendas ADD COLUMN validade_impressa TEXT",
        "ALTER TABLE tabelas_preco ADD COLUMN pct_contrato REAL DEFAULT 0.0",
        "ALTER TABLE tabelas_preco ADD COLUMN pct_comissao_auxiliar REAL DEFAULT 0.0",
        "ALTER TABLE tabelas_preco ADD COLUMN pct_acordo_logistico REAL DEFAULT 0.0",
        "ALTER TABLE vendas ADD COLUMN custo_acordos_rede REAL DEFAULT 0.0",
        "ALTER TABLE clientes ADD COLUMN taxa_descarga REAL DEFAULT 0.0",
        "ALTER TABLE clientes ADD COLUMN regras_descarga TEXT",
        "ALTER TABLE contas_a_pagar ADD COLUMN comprovante_url TEXT",
        "ALTER TABLE vendas ADD COLUMN custo_descarga REAL DEFAULT 0.0",
        "ALTER TABLE maquinario ADD COLUMN patrimônio TEXT",
        "ALTER TABLE maquinario ADD COLUMN numero_serie TEXT",
        "ALTER TABLE maquinario ADD COLUMN localizacao TEXT DEFAULT 'Fábrica'",
        "ALTER TABLE estoque_movimentos ADD COLUMN lote_origem_id INTEGER",
        "ALTER TABLE fluxo_caixa ADD COLUMN cliente_id INTEGER",
        "ALTER TABLE contas_a_pagar ADD COLUMN cliente_id INTEGER",
        "ALTER TABLE vendas ADD COLUMN is_bonificacao BOOLEAN DEFAULT 0",
        "ALTER TABLE vendas ADD COLUMN custo_cmv_real REAL DEFAULT 0.0",
        "ALTER TABLE planos_de_contas ADD COLUMN codigo TEXT",
        "ALTER TABLE empresa_config ADD COLUMN telefone TEXT",
        "ALTER TABLE empresa_config ADD COLUMN email TEXT",
        "ALTER TABLE empresa_config ADD COLUMN inscricao_estadual TEXT",
        "ALTER TABLE empresa_config ADD COLUMN inscricao_municipal TEXT",
        "ALTER TABLE empresa_config ADD COLUMN cep TEXT",
        "ALTER TABLE empresa_config ADD COLUMN instagram TEXT",
        "ALTER TABLE empresa_config ADD COLUMN website TEXT",
        "ALTER TABLE usuarios ADD COLUMN funcionario_id INTEGER"
    ]
    
    # Executar DDL de migração com autocommit na mesma conexão (evita esgotar o pool)
    import re as _re
    is_pg = init_connection_pool() is not None
    if is_pg:
        # Commita qualquer transação pendente antes de trocar para autocommit
        try:
            conn.commit()
        except Exception:
            pass
        conn.autocommit = True
        cur_ddl = conn.cursor()
        for q in alter_queries:
            q_pg = _re.sub(
                r'(?i)(ALTER\s+TABLE\s+\w+\s+ADD\s+COLUMN\s+)(?!IF\s+NOT\s+EXISTS\s+)',
                r'\1IF NOT EXISTS ',
                q.replace("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")
                 .replace("BOOLEAN DEFAULT 1", "BOOLEAN DEFAULT TRUE")
            )
            try:
                cur_ddl.execute(q_pg)
            except Exception:
                pass
        cur_ddl.close()
        conn.autocommit = False
    else:
        # SQLite: try/except por statement
        for q in alter_queries:
            try:
                conn.execute(q)
                conn.commit()
            except Exception:
                pass


def clean_params(params):
    if not isinstance(params, (list, tuple)):
        params = (params,)
    cleaned = []
    for p in params:
        if hasattr(p, 'item') and callable(getattr(p, 'item')):
            cleaned.append(p.item())
        else:
            cleaned.append(p)
    return tuple(cleaned)

def run_query(query, params=()):
    params = clean_params(params)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(format_pg(query), params)
        conn.commit()

def fetch_all(query, params=()):
    params = clean_params(params)
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(format_pg(query), params)
            data = cursor.fetchall()
            
            # Obter os nomes das colunas
            if cursor.description:
                cols = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(data, columns=cols)
            else:
                df = pd.DataFrame()
                
            cursor.close()
            return df
    except Exception as e:
        st.error(f"Erro no fetch_all: {e}")
        return pd.DataFrame()

def consumir_estoque_fifo(produto_id, quantidade, data_mov, origem, doc_ref):
    """
    Consome o estoque utilizando o algoritmo FIFO.
    Retorna uma tupla: (custo_total_acumulado, is_estimado)
    """
    # 1. Obter os lotes ativos com saldo físico disponível > 0 ordenados por data/ID (FIFO)
    query_lotes = """
        SELECT pd.id, pd.custo_unitario_lote, pd.data, pd.produto_final_kg,
               (pd.produto_final_kg - COALESCE((
                    SELECT SUM(em.quantidade) 
                    FROM estoque_movimentos em 
                    WHERE em.lote_origem_id = pd.id AND em.tipo_movimento = 'Saída'
               ), 0.0)) as saldo
        FROM producao_diaria pd
        WHERE pd.produto_id = ?
        ORDER BY pd.data ASC, pd.id ASC
    """
    df_lotes = fetch_all(query_lotes, (produto_id,))
    
    quantidade_restante = float(quantidade)
    custo_acumulado = 0.0
    is_estimado = False
    
    # Filtrar apenas linhas com saldo > 0 em Python (evita problemas de tipo com SQLite/Postgres)
    lotes_disponiveis = []
    if not df_lotes.empty:
        df_lotes['saldo'] = df_lotes['saldo'].astype(float)
        lotes_disponiveis = df_lotes[df_lotes['saldo'] > 0.0].to_dict('records')
        
    for lot in lotes_disponiveis:
        if quantidade_restante <= 0:
            break
            
        lote_id = int(lot['id'])
        custo_un_lote = float(lot['custo_unitario_lote'] or 0.0)
        saldo_lote = float(lot['saldo'])
        
        if saldo_lote >= quantidade_restante:
            # Consome tudo que resta do pedido deste lote
            run_query(
                """INSERT INTO estoque_movimentos 
                   (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id) 
                   VALUES (?, ?, 'Saída', ?, ?, ?, ?)""",
                (data_mov, produto_id, quantidade_restante, origem, doc_ref, lote_id)
            )
            custo_acumulado += quantidade_restante * custo_un_lote
            quantidade_restante = 0.0
            break
        else:
            # Consome o saldo total do lote e continua para o próximo
            run_query(
                """INSERT INTO estoque_movimentos 
                   (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id) 
                   VALUES (?, ?, 'Saída', ?, ?, ?, ?)""",
                (data_mov, produto_id, saldo_lote, origem, doc_ref, lote_id)
            )
            custo_acumulado += saldo_lote * custo_un_lote
            quantidade_restante -= saldo_lote
            
    # Se ainda restar quantidade (estoque no vermelho/negativo)
    if quantidade_restante > 0:
        is_estimado = True
        # Obter o custo unitário padrão cadastrado no produto
        df_prod = fetch_all("SELECT custo_unidade FROM produtos WHERE id = ?", (produto_id,))
        custo_padrao = float(df_prod.iloc[0]['custo_unidade'] or 0.0) if not df_prod.empty else 0.0
        
        run_query(
            """INSERT INTO estoque_movimentos 
               (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id) 
               VALUES (?, ?, 'Saída', ?, ?, ?, NULL)""",
            (data_mov, produto_id, quantidade_restante, origem, doc_ref)
        )
        custo_acumulado += quantidade_restante * custo_padrao
        quantidade_restante = 0.0
        
    return custo_acumulado, is_estimado

def gerar_comissao_se_necessario(venda_id, momento_gatilho, cliente_nome=None):
    """
    Gera o comissao_valor do vendedor se o momento do gatilho corresponder
    (momento_gatilho pode ser 'FATURAMENTO' ou 'LIQUIDAÇÃO DE TITULO').
    Salva o valor calculado diretamente no registro da venda para conferência posterior.
    """
    from datetime import date
    import calendar
    import pandas as pd
    
    # 1. Puxa vendedor, valor de comissão e cliente da venda
    df_venda = fetch_all('''
        SELECT v.vendedor_id, v.comissao_valor, v.cliente_id, v.produto_id, v.valor_total,
               c.nome as cliente_nome, COALESCE(c.rede_clientes, '') as rede_clientes
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.id = ?
    ''', (venda_id,))
    
    if df_venda.empty:
        return
        
    vendedor_id = int(df_venda.iloc[0]['vendedor_id'])
    comissao_val = float(df_venda.iloc[0]['comissao_valor'] or 0.0)
    cliente_id = int(df_venda.iloc[0]['cliente_id'])
    produto_id = int(df_venda.iloc[0]['produto_id']) if pd.notna(df_venda.iloc[0]['produto_id']) else None
    valor_total = float(df_venda.iloc[0]['valor_total'] or 0.0)
    cli_nome = cliente_nome if cliente_nome else df_venda.iloc[0]['cliente_nome']
    rede_c = df_venda.iloc[0]['rede_clientes']
    if not rede_c:
        rede_c = "TODOS"
        
    # 2. Busca regra do vendedor
    df_vend = fetch_all("SELECT gatilho_comissao, dia_vencimento_comissao, nome FROM funcionarios WHERE id = ?", (vendedor_id,))
    if df_vend.empty:
        return
        
    gatilho = str(df_vend.iloc[0]['gatilho_comissao'] or 'FATURAMENTO').upper()
    
    # Se o gatilho da regra não corresponder ao momento solicitado, ignora
    if momento_gatilho == 'FATURAMENTO' and "LIQUIDAÇÃO" in gatilho:
        return
    if momento_gatilho == 'LIQUIDAÇÃO' and "LIQUIDAÇÃO" not in gatilho:
        return
        
    # Se comissao_val for zero, tenta recalcular dinamicamente se existir uma regra cadastrada
    if comissao_val <= 0.0:
        df_regra = fetch_all('''
            SELECT percentual 
            FROM comissoes_regras 
            WHERE vendedor_id = ? 
              AND (produto_id = ? OR produto_id IS NULL)
              AND (rede_clientes = ? OR rede_clientes = 'TODOS')
            ORDER BY (CASE WHEN produto_id = ? THEN 2 ELSE 1 END) DESC,
                     (CASE WHEN rede_clientes = ? THEN 2 ELSE 1 END) DESC
            LIMIT 1
        ''', (vendedor_id, produto_id, rede_c, produto_id, rede_c))
        
        if not df_regra.empty:
            percentual = float(df_regra.iloc[0]['percentual'])
            comissao_val = valor_total * (percentual / 100.0)
            
    if comissao_val > 0.0:
        # Atualiza o valor na venda no banco para fins de DRE, auditoria e fechamento
        run_query("UPDATE vendas SET comissao_valor = ? WHERE id = ?", (comissao_val, venda_id))

if __name__ == "__main__":
    create_tables()
    print("Banco de dados configurado com sucesso!")
