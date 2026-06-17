from database import fetch_all

print("=== Vendas ===")
df_v = fetch_all("SELECT id, data, valor_total, comissao_valor FROM vendas")
print(df_v)

print("\n=== Contas a Pagar ===")
df_c = fetch_all("""
    SELECT c.id, c.data_vencimento, c.valor, pc.codigo, pc.nome 
    FROM contas_a_pagar c
    JOIN planos_de_contas pc ON c.plano_conta_id = pc.id
""")
print(df_c)
