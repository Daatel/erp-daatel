from database import fetch_all

print("--- Vendas Months ---")
df_v = fetch_all("SELECT DISTINCT strftime('%Y-%m', data) as mes, count(*) as total FROM vendas GROUP BY mes")
print(df_v)

print("--- Contas a Pagar Months ---")
df_c = fetch_all("SELECT DISTINCT strftime('%Y-%m', data_vencimento) as mes, count(*) as total FROM contas_a_pagar GROUP BY mes")
print(df_c)
