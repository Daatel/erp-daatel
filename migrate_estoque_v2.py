import sqlite3
import os

DB_NAME = r"C:\Users\MARCIO\Gestao_Fabrica_Alho\erp_fabrica.db"

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("Iniciando migração de estoque...")
    
    try:
        cursor.execute("ALTER TABLE estoque_movimentos ADD COLUMN plano_conta_id INTEGER")
        print("Coluna 'plano_conta_id' adicionada em 'estoque_movimentos'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Coluna 'plano_conta_id' já existe.")
        else:
            print("Erro ao adicionar 'plano_conta_id':", e)

    try:
        cursor.execute("ALTER TABLE estoque_movimentos ADD COLUMN documento_referencia TEXT")
        print("Coluna 'documento_referencia' adicionada em 'estoque_movimentos'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Coluna 'documento_referencia' já existe.")
        else:
            print("Erro ao adicionar 'documento_referencia':", e)

    try:
        cursor.execute("ALTER TABLE produtos ADD COLUMN estoque_minimo REAL DEFAULT 0.0")
        print("Coluna 'estoque_minimo' adicionada em 'produtos'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Coluna 'estoque_minimo' já existe.")
        else:
            print("Erro ao adicionar 'estoque_minimo':", e)

    conn.commit()
    conn.close()
    print("Migração finalizada com sucesso!")

if __name__ == "__main__":
    migrate()
