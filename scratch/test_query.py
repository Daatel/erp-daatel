from database import fetch_all
import pandas as pd

df = fetch_all("SELECT count(*) as total FROM contas_a_pagar")
print("Total contas_a_pagar:", df['total'].iloc[0] if not df.empty else 0)

df_sample = fetch_all("""
    SELECT c.valor, c.data_vencimento, pc.codigo, pc.categoria, pc.nome
    FROM contas_a_pagar c
    JOIN planos_de_contas pc ON c.plano_conta_id = pc.id
    LIMIT 10
""")
print(df_sample)
