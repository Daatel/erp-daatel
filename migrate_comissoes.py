import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def run_migration():
    if not os.path.exists(DB_NAME):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(comissoes_regras)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "rede_clientes" not in columns:
        print("Adicionando coluna rede_clientes...")
        cursor.execute("ALTER TABLE comissoes_regras ADD COLUMN rede_clientes TEXT")
    else:
        print("Coluna rede_clientes já existe.")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    run_migration()
