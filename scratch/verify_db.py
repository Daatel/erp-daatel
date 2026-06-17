import sqlite3
import pandas as pd
from database import initialize_database, db_connection, init_connection_pool

print("Initializing database...")
initialize_database()

is_pg = init_connection_pool() is not None
print("Database is PostgreSQL:", is_pg)

with db_connection() as conn:
    cursor = conn.cursor()
    
    if is_pg:
        # PostgreSQL check
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'clientes'")
        cols_cli = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'fornecedores'")
        cols_forn = [row[0] for row in cursor.fetchall()]
    else:
        # SQLite check
        cursor.execute("PRAGMA table_info(clientes)")
        cols_cli = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(fornecedores)")
        cols_forn = [row[1] for row in cursor.fetchall()]
        
    print("Clientes columns:", cols_cli)
    print("Fornecedores columns:", cols_forn)
    
    # Assert chave_pix exists in both
    assert "chave_pix" in cols_cli, "chave_pix missing in clientes"
    assert "chave_pix" in cols_forn, "chave_pix missing in fornecedores"
    print("✅ All columns migrated successfully!")
