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
    "empresa_config"
]

DEFAULT_USERS = [
    ('Diretor Márcio', 'admin@alho.com', 'admin123', 'ADMIN', 'ATIVO'),
    ('Vendedor', 'vendas@alho.com', 'vend123', 'VENDAS', 'ATIVO'),
    ('Produção', 'fabrica@alho.com', 'fab123', 'PRODUCAO', 'ATIVO'),
    ('Financeiro', 'fin@alho.com', 'fin123', 'FINANCEIRO', 'ATIVO'),
    ('Compras', 'compras@alho.com', 'comp123', 'COMPRAS', 'ATIVO')
]

DEFAULT_PLANOS_DE_CONTAS = [
    ("RECEITA",    "Venda de Produtos"),
    ("RECEITA",    "Venda de Subprodutos"),
    ("CMV",        "Custo da Mercadoria Vendida"),
    ("CMV",        "Custo da Embalagem"),
    ("COMPRA",     "Compra de Matéria-Prima"),
    ("COMPRA",     "Compra de Embalagens"),
    ("COMPRA",     "Compra de Insumos"),
    ("DESPESA_OP", "Frete e Logística"),
    ("DESPESA_OP", "Manutenção de Equipamentos"),
    ("DESPESA_OP", "Energia Elétrica"),
    ("DESPESA_OP", "Aluguel"),
    ("RH",         "Salários e Encargos"),
    ("RH",         "Comissões de Vendas"),
    ("ACORDOS",    "Taxa de Descarga"),
    ("ACORDOS",    "Acordo Logístico / Rebate de Rede"),
    ("ACORDOS",    "Contrato Comercial"),
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
            "INSERT INTO planos_de_contas (categoria, nome) VALUES (?,?)",
            DEFAULT_PLANOS_DE_CONTAS
        )
        print("  [SQLite] Planos de contas padrão reinseridos.")
        
        # 3. Inserir usuários padrão
        cur.executemany(
            "INSERT INTO usuarios (nome, email, senha, nivel_permissao, status) VALUES (?, ?, ?, ?, ?)",
            DEFAULT_USERS
        )
        print("  [SQLite] Usuários de login reinseridos.")
        
        # 4. Configuração básica da empresa
        cur.execute(
            "INSERT INTO empresa_config (razao_social, nome_fantasia, cnpj, endereco_completo) VALUES (?, ?, ?, ?)",
            ('Empório do Alho LTDA', 'Empório do Alho', '00.000.000/0001-00', 'Rua Principal, 123 - Centro')
        )
        print("  [SQLite] Empresa padrão configurada.")
        
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
            "INSERT INTO planos_de_contas (categoria, nome) VALUES (%s, %s)",
            DEFAULT_PLANOS_DE_CONTAS
        )
        print("  [Supabase] Planos de contas padrão reinseridos.")
        
        # 3. Inserir usuários padrão
        cur.executemany(
            "INSERT INTO usuarios (nome, email, senha, nivel_permissao, status) VALUES (%s, %s, %s, %s, %s)",
            DEFAULT_USERS
        )
        print("  [Supabase] Usuários de login reinseridos.")
        
        # 4. Configuração básica da empresa
        cur.execute(
            "INSERT INTO empresa_config (razao_social, nome_fantasia, cnpj, endereco_completo) VALUES (%s, %s, %s, %s)",
            ('Empório do Alho LTDA', 'Empório do Alho', '00.000.000/0001-00', 'Rua Principal, 123 - Centro')
        )
        print("  [Supabase] Empresa padrão configurada.")
        
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
