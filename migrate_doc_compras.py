import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def run_migration():
    if not os.path.exists(DB_NAME): return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(compras)")
    cols = [info[1] for info in cursor.fetchall()]
    if "tipo_doc" not in cols:
        cursor.execute("ALTER TABLE compras ADD COLUMN tipo_doc TEXT")
    if "numero_doc" not in cols:
        cursor.execute("ALTER TABLE compras ADD COLUMN numero_doc TEXT")
    conn.commit()
    conn.close()
    print("Migração Compras Docs finalizada!")

if __name__ == '__main__':
    run_migration()
