import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def run_migration():
    if not os.path.exists(DB_NAME):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(fornecedores)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "prazo_pagamento" not in columns:
        print("Adicionando coluna prazo_pagamento em fornecedores...")
        cursor.execute("ALTER TABLE fornecedores ADD COLUMN prazo_pagamento TEXT")
    else:
        print("Coluna prazo_pagamento já existe.")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    run_migration()
