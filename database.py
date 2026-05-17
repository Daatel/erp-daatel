import sqlite3
import pandas as pd
import os
import streamlit as st

DB_NAME = "erp_fabrica.db"

@st.cache_resource
def init_connection_pool():
    if "DATABASE_URL" in st.secrets:
        from psycopg2 import pool
        # Cria um pool thread-safe com até 10 conexões reaproveitáveis
        return pool.ThreadedConnectionPool(1, 10, st.secrets["DATABASE_URL"])
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

def format_pg(sql):
    if "DATABASE_URL" in st.secrets:
        sql = sql.replace("?", "%s")
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        sql = sql.replace("DATETIME DEFAULT CURRENT_TIMESTAMP", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        sql = sql.replace("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")
        sql = sql.replace("BOOLEAN DEFAULT 1", "BOOLEAN DEFAULT TRUE")
        
        # Remove FOREIGN KEY para evitar erro de ordem (relação não existe)
        linhas = []
        for linha in sql.split('\n'):
            if "FOREIGN KEY" not in linha.upper():
                linhas.append(linha)
        sql = '\n'.join(linhas)
        import re
        sql = re.sub(r",\s*\)", "\n    )", sql)
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
        FOREIGN KEY(conta_bancaria_id) REFERENCES contas_bancarias(id)
    )
    ''')

    # 12. Planos de Contas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS planos_de_contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        nome TEXT NOT NULL,
        email TEXT UNIQUE,
        senha TEXT NOT NULL,
        nivel_permissao TEXT NOT NULL,
        status TEXT DEFAULT 'ATIVO'
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
        email TEXT
    )
    ''')
    
    # Inserir empresa padrão se não existir
    cursor.execute("SELECT COUNT(*) FROM empresa_config")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO empresa_config (razao_social, nome_fantasia, cnpj, endereco_completo) VALUES ('Empório do Alho LTDA', 'Empório do Alho', '00.000.000/0001-00', 'Rua Principal, 123 - Centro')")

    # Migração: Adicionar colunas se não existirem
    try:
        cursor.execute("ALTER TABLE compras_itens ADD COLUMN unidade TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE compras_itens ADD COLUMN quantidade_estoque REAL")
    except: pass
    try:
        cursor.execute("ALTER TABLE compras_itens ADD COLUMN produto_nome TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE produtos ADD COLUMN embalagem_master TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE produtos ADD COLUMN cod_emb_master TEXT")
    except: pass
    try:
        cursor.execute("ALTER TABLE producao_diaria ADD COLUMN custo_total_lote REAL")
    except: pass
    try:
        cursor.execute("ALTER TABLE producao_diaria ADD COLUMN custo_unitario_lote REAL")
    except: pass
    try:
        cursor.execute("ALTER TABLE producao_diaria ADD COLUMN data_validade DATE")
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE vendas ADD COLUMN lote_impresso TEXT"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE vendas ADD COLUMN validade_impressa TEXT"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE tabelas_preco ADD COLUMN pct_contrato REAL DEFAULT 0.0"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE tabelas_preco ADD COLUMN pct_comissao_auxiliar REAL DEFAULT 0.0"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE tabelas_preco ADD COLUMN pct_acordo_logistico REAL DEFAULT 0.0"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE vendas ADD COLUMN custo_acordos_rede REAL DEFAULT 0.0"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE clientes ADD COLUMN taxa_descarga REAL DEFAULT 0.0"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE clientes ADD COLUMN regras_descarga TEXT"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE contas_a_pagar ADD COLUMN comprovante_url TEXT"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE vendas ADD COLUMN custo_descarga REAL DEFAULT 0.0"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE maquinario ADD COLUMN patrimônio TEXT"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE maquinario ADD COLUMN numero_serie TEXT"))
    except: pass
    try:
        cursor.execute(format_pg("ALTER TABLE maquinario ADD COLUMN localizacao TEXT DEFAULT 'Fábrica'"))
    except: pass

    conn.commit()
    release_connection(conn)

def run_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(format_pg(query), params)
    conn.commit()
    release_connection(conn)

def fetch_all(query, params=()):
    conn = get_connection()
    try:
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
    finally:
        release_connection(conn)

if __name__ == "__main__":
    create_tables()
    print("Banco de dados configurado com sucesso!")
