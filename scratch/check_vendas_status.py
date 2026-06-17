from database import fetch_all

df = fetch_all("SELECT id, status, data, valor_total FROM vendas")
print(df)
