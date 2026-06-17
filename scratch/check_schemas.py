from database import fetch_all
import sqlite3

conn = sqlite3.connect("erp_fabrica.db")
cursor = conn.cursor()

def print_table_info(table_name):
    print(f"=== Table: {table_name} ===")
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Col {col[0]}: {col[1]} ({col[2]})")
    except Exception as e:
        print("Error:", e)

print_table_info("clientes")
print_table_info("fornecedores")
print_table_info("funcionarios")

conn.close()
