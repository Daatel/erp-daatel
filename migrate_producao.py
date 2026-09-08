import sqlite3

def run_migration():
    conn = sqlite3.connect("erp_fabrica.db")
    cursor = conn.cursor()

    try:
        # Add Time Columns to producao_diaria
        cursor.execute("ALTER TABLE producao_diaria ADD COLUMN hora_inicio TIME;")
    except sqlite3.OperationalError:
        print("Coluna hora_inicio ja existe.")

    try:
        cursor.execute("ALTER TABLE producao_diaria ADD COLUMN hora_fim TIME;")
    except sqlite3.OperationalError:
        print("Coluna hora_fim ja existe.")

    # Create producao_insumos relation table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS producao_insumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producao_id INTEGER,
            produto_id INTEGER,
            quantidade REAL,
            FOREIGN KEY(producao_id) REFERENCES producao_diaria(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    ''')

    # Add tables to database.py create_tables definition
    with open("database.py", "r", encoding="utf-8") as f:
        db_content = f.read()

    if "producao_insumos" not in db_content:
        # We need to manually inject it or just let the database run the script and then modify database.py
        pass

    conn.commit()
    conn.close()
    print("Migration Producao finalizada.")

if __name__ == "__main__":
    run_migration()
