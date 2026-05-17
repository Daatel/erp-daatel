import sqlite3

def fix_users():
    conn = sqlite3.connect('erp_fabrica.db')
    cur = conn.cursor()
    
    users_to_add = [
        ('Diretor Márcio', 'admin@alho.com', 'admin123', 'ADMIN', 'ATIVO'),
        ('Vendedor Silva', 'vendas@alho.com', 'vend123', 'VENDAS', 'ATIVO'),
        ('Operador Fábrica', 'fabrica@alho.com', 'fab123', 'PRODUCAO', 'ATIVO'),
        ('Financeiro', 'fin@alho.com', 'fin123', 'FINANCEIRO', 'ATIVO')
    ]
    
    for user in users_to_add:
        try:
            cur.execute("INSERT INTO usuarios (nome, email, senha, nivel_permissao, status) VALUES (?, ?, ?, ?, ?)", user)
        except Exception as e:
            print(f"Error inserting {user[1]}: {e}")
            
    conn.commit()
    cur.execute('SELECT email FROM usuarios')
    print("Usuarios no banco:", cur.fetchall())
    conn.close()

if __name__ == '__main__':
    fix_users()
