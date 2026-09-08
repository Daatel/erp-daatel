import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def run_migration():
    if not os.path.exists(DB_NAME):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS planos_de_contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT NOT NULL,
        nome TEXT NOT NULL
    )
    ''')
    
    cursor.execute("SELECT Count(*) FROM planos_de_contas")
    if cursor.fetchone()[0] == 0:
        contas = [
            ("Receita Com Vendas", "Venda de Produtos"),
            ("Receita Operacional", "Outras Receitas"),
            ("Custo Variável", "MATERIA PRIMA"),
            ("Custo Variável", "Embalagens e Insumos"),
            ("Custo Variável", "Fretes de Entrega"),
            ("Custo Variável", "Comissões de Vendas"),
            ("Custo Variável", "Impostos sobre Venda (Simples/ICMS)"),
            ("Despesa Fixa", "Energia Elétrica"),
            ("Despesa Fixa", "Água e Esgoto"),
            ("Despesa Fixa", "Aluguel e IPTU"),
            ("Despesa Fixa", "Pró-Labore Sócios"),
            ("Despesa Fixa", "Salários e Encargos"),
            ("Despesa Fixa", "Manutenção de Máquinas"),
            ("Despesa Fixa", "Material de Limpeza / EPI"),
            ("Despesa Fixa", "Material de Escritório"),
            ("Despesa Fixa", "Assessoria Contábil e Jurídica"),
            ("Despesa Fixa", "Internet e Telefonia"),
            ("Despesa Financeira", "Taxas Bancárias e Maquininhas"),
            ("Despesa Financeira", "Juros e Empréstimos"),
            ("Investimento", "Aquisição de Máquinas"),
            ("Investimento", "Reformas Estruturais")
        ]
        
        cursor.executemany("INSERT INTO planos_de_contas (categoria, nome) VALUES (?, ?)", contas)
        print("Planos de contas oficiais inseridos com sucesso!")
    else:
        print("Tabela planos_de_contas já possui dados.")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    run_migration()
