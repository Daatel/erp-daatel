import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def add_columns_safe():
    if not os.path.exists(DB_NAME):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(fornecedores)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if not columns: return

    new_cols = {
        'nome_fantasia': 'TEXT',
        'inscricao_estadual': 'TEXT',
        'endereco': 'TEXT',
        'bairro': 'TEXT',
        'cep': 'TEXT',
        'cidade': 'TEXT',
        'uf': 'TEXT',
        'email': 'TEXT',
        'plano_de_contas': 'TEXT',
        'status': 'TEXT'
    }
    
    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            print(f"Adicionando coluna {col_name}...")
            cursor.execute(f"ALTER TABLE fornecedores ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("Migração de fornecedores concluída!")

if __name__ == '__main__':
    add_columns_safe()
