import sqlite3
import pandas as pd
import tomllib
import os
from sqlalchemy import create_engine

DB_NAME = "erp_fabrica.db"

def migrate():
    print("Iniciando migração do SQLite local para o Supabase (PostgreSQL)...")
    
    # 1. Carregar configuração
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        print("Erro: Arquivo secrets.toml não encontrado.")
        return
        
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    pg_url = secrets.get("DATABASE_URL")
    if not pg_url or "COLOQUE_SUA_SENHA_AQUI" in pg_url:
        print("Erro: Senha não configurada no secrets.toml")
        return
        
    print("1. Conectando aos bancos...")
    # SQLite
    sqlite_conn = sqlite3.connect(DB_NAME)
    
    # PostgreSQL Engine
    engine_url = pg_url.replace("postgres://", "postgresql://")
    pg_engine = create_engine(engine_url)
    
    # 2. Ler todas as tabelas do SQLite
    print("2. Lendo tabelas do SQLite...")
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_names = [t[0] for t in tables if t[0] != "sqlite_sequence"]
    
    dataframes = {}
    for table in table_names:
        df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
        dataframes[table] = df
        print(f"   - Tabela {table} carregada ({len(df)} linhas)")
        
    # 3. Criar a estrutura no Postgres
    print("3. Criando estrutura (Schema) no Supabase...")
    # We must use database.py with secrets loaded
    import streamlit as st
    st.secrets = {"DATABASE_URL": pg_url}
    from database import create_tables
    
    create_tables()
    print("   - Estrutura criada com sucesso.")
    
    # 4. Inserir dados no Postgres
    print("4. Migrando os dados para o Supabase...")
    for table in table_names:
        df = dataframes[table]
        if not df.empty:
            try:
                df.to_sql(table, pg_engine, if_exists='append', index=False)
                print(f"   [OK] {table} -> {len(df)} registros migrados.")
            except Exception as e:
                print(f"   [ERRO] Falha ao migrar {table}: {e}")
                
    print("Migração concluída com sucesso! 🎉")

if __name__ == "__main__":
    migrate()
