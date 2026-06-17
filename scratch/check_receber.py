from database import fetch_all

df = fetch_all("SELECT * FROM contas_a_receber LIMIT 3")
print("Contas a Receber:")
print(df.columns.tolist())
print(df)
