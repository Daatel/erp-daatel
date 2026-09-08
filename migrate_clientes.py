import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def add_columns_safe():
    if not os.path.exists(DB_NAME):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(clientes)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if not columns: return

    new_cols = {
        'nome_fantasia': 'TEXT',
        'cnpj_cpf': 'TEXT',
        'inscricao_estadual': 'TEXT',
        'bairro': 'TEXT',
        'cep': 'TEXT',
        'cidade': 'TEXT',
        'uf': 'TEXT',
        'email': 'TEXT',
        'observacoes': 'TEXT',
        'status': 'TEXT',
        'rede_clientes': 'TEXT',
        'grupo_lojas': 'TEXT',
        'prazo_pagamento': 'TEXT',
        'representante_id': 'INTEGER REFERENCES funcionarios(id)'
    }
    
    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            print(f"Adicionando coluna {col_name}...")
            cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("Migração de clientes concluída!")

if __name__ == '__main__':
    add_columns_safe()
