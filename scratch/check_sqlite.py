import sqlite3
import pandas as pd

conn = sqlite3.connect("erp_fabrica.db")
df = pd.read_sql("SELECT id, data, valor_total, comissao_valor, status FROM vendas", conn)
print(df)
conn.close()
