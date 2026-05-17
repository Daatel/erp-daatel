import sqlite3
import os

DB_NAME = "C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db"

def run_migration():
    if not os.path.exists(DB_NAME): return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabela Contas Bancárias
    cursor.execute('''CREATE TABLE IF NOT EXISTS contas_bancarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        banco TEXT,
        agencia TEXT,
        conta TEXT,
        saldo_inicial REAL DEFAULT 0.0,
        tipo_conta TEXT,
        status TEXT DEFAULT 'ATIVO'
    )''')
    
    # Check if we have at least 'Caixa / Tesouraria'
    cursor.execute("SELECT id FROM contas_bancarias WHERE nome = 'Caixa / Tesouraria'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO contas_bancarias (nome, tipo_conta, saldo_inicial) VALUES ('Caixa / Tesouraria', 'Espécie', 0.0)")
    
    # 2. Tabela Contas a Receber
    cursor.execute('''CREATE TABLE IF NOT EXISTS contas_a_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER,
        cliente_id INTEGER,
        plano_conta_id INTEGER,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data_vencimento DATE NOT NULL,
        data_recebimento DATE,
        status TEXT NOT NULL DEFAULT 'PENDENTE',
        conta_bancaria_id INTEGER,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(conta_bancaria_id) REFERENCES contas_bancarias(id)
    )''')
    
    # 3. Altering Fluxo de Caixa
    cursor.execute("PRAGMA table_info(fluxo_caixa)")
    cols_caixa = [info[1] for info in cursor.fetchall()]
    if "conta_bancaria_id" not in cols_caixa:
        cursor.execute("ALTER TABLE fluxo_caixa ADD COLUMN conta_bancaria_id INTEGER REFERENCES contas_bancarias(id)")
    if "conciliado" not in cols_caixa:
        cursor.execute("ALTER TABLE fluxo_caixa ADD COLUMN conciliado BOOLEAN DEFAULT 0")
        
    # Set default conta for existing fluxo
    cursor.execute("UPDATE fluxo_caixa SET conta_bancaria_id = 1 WHERE conta_bancaria_id IS NULL")
        
    # 4. Altering Contas a Pagar
    cursor.execute("PRAGMA table_info(contas_a_pagar)")
    cols_pagar = [info[1] for info in cursor.fetchall()]
    if "conta_bancaria_id" not in cols_pagar:
        cursor.execute("ALTER TABLE contas_a_pagar ADD COLUMN conta_bancaria_id INTEGER REFERENCES contas_bancarias(id)")

    conn.commit()
    conn.close()
    print("Migracao Multi-Bancos Concluida com Sucesso!")

if __name__ == '__main__':
    run_migration()
