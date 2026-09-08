import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def add_columns_safe():
    if not os.path.exists(DB_NAME):
        print("Banco de dados não existe ainda, nenhuma migração necessária.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Pega as colunas existentes da tabela produtos
    cursor.execute("PRAGMA table_info(produtos)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # Caso a tabela não exista ainda (ex: db acabou de ser criado sem rodar create_tables)
    if not columns:
        print("A tabela 'produtos' não existe. Faça no app.py a criação das tabelas.")
        return

    # Definimos as novas colunas que vieram do Google Sheets
    new_cols = {
        'marca': 'TEXT',
        'peso_volume': 'TEXT',
        'referencia': 'TEXT',
        'ean': 'TEXT',
        'unidades_por_fardo': 'INTEGER',
        'tipo_embalagem': 'TEXT',
        'custo_unidade': 'REAL DEFAULT 0.0',
        'custo_fardo': 'REAL DEFAULT 0.0'
    }
    
    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            print(f"Adicionando coluna {col_name}...")
            cursor.execute(f"ALTER TABLE produtos ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("Migração concluída com sucesso!")

if __name__ == '__main__':
    add_columns_safe()
