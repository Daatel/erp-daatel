import sqlite3

DB_NAME = r"C:\Users\MARCIO\Gestao_Fabrica_Alho\erp_fabrica.db"

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("Iniciando migração de vendas (Status de Faturamento)...")
    
    try:
        # Adiciona a coluna com valor padrão FATURADO para não quebrar o histórico de vendas antigas que já bateram no caixa/estoque
        cursor.execute("ALTER TABLE vendas ADD COLUMN status TEXT DEFAULT 'FATURADO'")
        print("Coluna 'status' adicionada em 'vendas'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Coluna 'status' já existe.")
        else:
            print("Erro ao adicionar 'status':", e)

    conn.commit()
    conn.close()
    print("Migração finalizada com sucesso!")

if __name__ == "__main__":
    migrate()
