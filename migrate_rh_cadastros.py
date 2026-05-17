import sqlite3
import os

DB_NAME = "C:\\Users\\MARCIO\\Gestao_Fabrica_Alho\\erp_fabrica.db"

def run_migration():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create Redes and Grupos
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

    # Add columns to clientes
    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN data_nascimento DATE;")
    except sqlite3.OperationalError:
        pass # Column might already exist

    # Add columns to funcionarios
    try:
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN data_nascimento DATE;")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN ajuda_custo REAL DEFAULT 0.0;")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN outros_valor REAL DEFAULT 0.0;")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN outros_descricao TEXT;")
    except sqlite3.OperationalError:
        pass

    # Add columns to comissoes_regras
    try:
        cursor.execute("ALTER TABLE comissoes_regras ADD COLUMN gatilho_comissao TEXT DEFAULT 'FATURAMENTO';")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE comissoes_regras ADD COLUMN minimo_garantido BOOLEAN DEFAULT 0;")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE comissoes_regras ADD COLUMN valor_minimo_garantido REAL DEFAULT 0.0;")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    run_migration()
