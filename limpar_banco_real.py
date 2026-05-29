import sqlite3
import os
import tomllib
import psycopg2
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_NAME = "erp_fabrica.db"

# Tabelas que devem ser totalmente limpas
TABELAS_PARA_LIMPAR = [
    "producao_insumos",
    "producao_diaria",
    "compras_itens",
    "compras_materia_prima",
    "compras",
    "contas_a_pagar",
    "contas_a_receber",
    "estoque_movimentos",
    "vendas",
    "manifestos_carga",
    "fluxo_caixa",
    "rh_pagamentos",
    "devolucoes",
    "tabelas_preco",
    "comissoes_regras",
    "funcionarios",
    "clientes",
    "fornecedores",
    "produtos",
    "maquinario",
    "redes_clientes",
    "grupos_clientes",
    "contas_bancarias",
    "fichas_tecnicas",
    "fichas_tecnicas_itens",
    "comodatos",
    "usuarios",
    "planos_de_contas"
]

DEFAULT_USERS = [
    ('Consultor Márcio', 'admin@alho.com', 'admin123', 'ADMIN', 'ATIVO'),
    ('Vendedor', 'vendas@alho.com', 'vend123', 'VENDAS', 'ATIVO'),
    ('Produção', 'fabrica@alho.com', 'fab123', 'PRODUCAO', 'ATIVO'),
    ('Financeiro', 'fin@alho.com', 'fin123', 'FINANCEIRO', 'ATIVO'),
    ('Compras', 'compras@alho.com', 'comp123', 'COMPRAS', 'ATIVO')
]

DEFAULT_PLANOS_DE_CONTAS = [
    # 1. Entradas (Receitas)
    ("1.1.1", "RECEITA", "Venda de Alho in natura"),
    ("1.1.2", "RECEITA", "Venda de alho descascado"),
    ("1.1.3", "RECEITA", "Venda de Temperos de alho"),
    ("1.1.4", "RECEITA", "Venda de alho frito"),
    ("1.1.5", "RECEITA", "outros"),
    ("1.2.1", "RECEITA_NAO_OP", "Entrada de Empréstimos Bancários"),
    ("1.2.2", "RECEITA_NAO_OP", "Aportes de Capital"),
    ("1.2.3", "RECEITA_NAO_OP", "Venda de Ativos (Máquinas/Veículos)"),

    # 2. Saídas Operacionais (Custos e Despesas)
    # 2.1. Custos Variáveis
    ("2.1.1", "CUSTO_VAR", "Compra de Matéria-Prima (Alho, Insumos)"),
    ("2.1.2", "CUSTO_VAR", "Compra de Embalagens (Potes, Caixas, Redes)"),
    ("2.1.3", "CUSTO_VAR", "Impostos sobre Vendas (Simples Nacional, etc.)"),
    ("2.1.4", "CUSTO_VAR", "Comissões de Vendas"),
    ("2.1.5", "CUSTO_VAR", "Fretes sobre Vendas (Entregas)"),
    # 2.2. Despesas Comerciais e Marketing
    ("2.2.1", "DESPESA_COM", "Custo de Degustações e Amostras"),
    ("2.2.2", "DESPESA_COM", "Contratos Comerciais (Enxoval, Listing Fee, Rapel)"),
    ("2.2.3", "DESPESA_COM", "Marketing e Feiras"),
    ("2.2.4", "DESPESA_COM", "Custos de Promotores de Vendas (Diárias, Agências e Serviços)"),
    # 2.3. Despesas Operacionais Fixas
    ("2.3.1", "DESPESA_FIXA", "Energia Elétrica, Água, Internet da Fábrica"),
    ("2.3.2", "DESPESA_FIXA", "Aluguel, IPTU, Seguros"),
    ("2.3.3", "DESPESA_FIXA", "Manutenção de Máquinas e Utensílios"),
    ("2.3.4", "DESPESA_FIXA", "Combustível, Pedágio e Manutenção de Veículos"),
    ("2.3.5", "DESPESA_FIXA", "Salários da Equipe Fabril (Mão de Obra Fixa)"),
    ("2.3.6", "DESPESA_FIXA", "Encargos Sociais, Provisões e Benefícios (VR, VT)"),

    # 3. Despesas Administrativas e Outras Saídas
    # 3.1. Despesas Administrativas
    ("3.1.1", "DESPESA_ADM", "Escritório, Papelaria, Software ERP, Licenças"),
    ("3.1.2", "DESPESA_ADM", "Honorários Contábeis e Advocatícios"),
    ("3.1.3", "DESPESA_ADM", "Tarifas e Taxas Bancárias"),
    ("3.1.4", "DESPESA_ADM", "Retirada de Pró-labore dos Sócios"),
    ("3.1.5", "DESPESA_ADM", "Salários e Encargos da Equipe Administrativa"),
    # 3.2. Despesas Não Operacionais
    ("3.2.1", "DESPESA_NAO_OP", "Pagamento de Empréstimos Bancários (Amortização)"),
    ("3.2.2", "DESPESA_NAO_OP", "Impostos e Taxas Extraordinárias"),
    # 3.3. Investimentos
    ("3.3.1", "INVESTIMENTO", "Compra de Máquinas, Freezers em Comodato ou Veículos")
]

def load_pg_url():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        return None
    try:
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        return secrets.get("DATABASE_URL")
    except Exception as e:
        print(f"Erro ao ler secrets.toml: {e}")
        return None

def limpar_sqlite():
    print(f"\n--- Limpando SQLite Local ({DB_NAME}) ---")
    if not os.path.exists(DB_NAME):
        print(f"Banco local '{DB_NAME}' não existe. Ignorando...")
        return
        
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()
    
    try:
        # 1. Limpar tabelas
        for t in TABELAS_PARA_LIMPAR:
            try:
                cur.execute(f"DELETE FROM {t}")
                print(f"  [SQLite] Tabela {t} limpa.")
            except Exception as e:
                print(f"  [SQLite] Erro ao limpar {t}: {e}")
                
        # Zera auto-increment
        try:
            cur.execute("DELETE FROM sqlite_sequence")
            print("  [SQLite] Sequências de auto-incremento reiniciadas.")
        except Exception as e:
            print(f"  [SQLite] Erro ao zerar sequências: {e}")
            
        # 2. Inserir planos de contas estruturais
        cur.executemany(
            "INSERT INTO planos_de_contas (codigo, categoria, nome) VALUES (?,?,?)",
            DEFAULT_PLANOS_DE_CONTAS
        )
        print("  [SQLite] Planos de contas padrão reinseridos.")
        
        # 3. Inserir usuários padrão
        cur.executemany(
            "INSERT INTO usuarios (nome, email, senha, nivel_permissao, status) VALUES (?, ?, ?, ?, ?)",
            DEFAULT_USERS
        )
        print("  [SQLite] Usuários de login reinseridos.")
        
        # 4. Configuração básica da empresa (preservada para proteger o cadastro personalizado)
        print("  [SQLite] Cadastro de Empresa preservado.")
        
        conn.commit()
        print("[OK] SQLite limpo e reconfigurado com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"[ERRO] Erro fatal no SQLite: {e}")
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

def limpar_postgresql(pg_url):
    print(f"\n--- Limpando PostgreSQL Nuvem (Supabase) ---")
    try:
        conn = psycopg2.connect(pg_url)
        cur = conn.cursor()
        
        # 1. Truncar tabelas usando CASCADE para lidar com chaves estrangeiras de forma elegante
        # Em PostgreSQL, podemos fazer um único TRUNCATE com CASCADE
        tabelas_str = ", ".join(TABELAS_PARA_LIMPAR)
        try:
            cur.execute(f"TRUNCATE TABLE {tabelas_str} RESTART IDENTITY CASCADE;")
            print("  [Supabase] Todas as tabelas limpas e IDs reiniciados via TRUNCATE CASCADE.")
        except Exception as e:
            conn.rollback()
            print(f"  [Supabase] Falha no TRUNCATE CASCADE ({e}). Tentando DELETE individual...")
            
            # Fallback para DELETE individual
            for t in TABELAS_PARA_LIMPAR:
                try:
                    cur.execute(f"DELETE FROM {t};")
                    print(f"  [Supabase] Tabela {t} limpa via DELETE.")
                except Exception as e2:
                    print(f"  [Supabase] Erro ao deletar {t}: {e2}")
                    conn.rollback()
        
        # 2. Inserir planos de contas estruturais
        cur.executemany(
            "INSERT INTO planos_de_contas (codigo, categoria, nome) VALUES (%s, %s, %s)",
            DEFAULT_PLANOS_DE_CONTAS
        )
        print("  [Supabase] Planos de contas padrão reinseridos.")
        
        # 3. Inserir usuários padrão
        cur.executemany(
            "INSERT INTO usuarios (nome, email, senha, nivel_permissao, status) VALUES (%s, %s, %s, %s, %s)",
            DEFAULT_USERS
        )
        print("  [Supabase] Usuários de login reinseridos.")
        
        # 4. Configuração básica da empresa (preservada para proteger o cadastro personalizado)
        print("  [Supabase] Cadastro de Empresa preservado.")
        
        conn.commit()
        print("[OK] PostgreSQL (Supabase) limpo e reconfigurado com sucesso!")
    except Exception as e:
        print(f"[ERRO] Erro fatal no PostgreSQL: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  PREPARANDO BANCO DE DADOS PARA PRODUÇÃO (DADOS REAIS)")
    print("=" * 60)
    
    # 1. Limpar SQLite Local
    limpar_sqlite()
    
    # 2. Limpar PostgreSQL Nuvem se configurado
    pg_url = load_pg_url()
    if pg_url:
        limpar_postgresql(pg_url)
    else:
        print("\n[AVISO] PostgreSQL não configurado no secrets.toml. Operação realizada apenas localmente.")
        
    print("\n" + "=" * 60)
    print("  BANCOS DE DADOS PRONTOS PARA CADASTROS REAIS! [OK]")
    print("=" * 60)
