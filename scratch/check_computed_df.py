import pandas as pd
from database import fetch_all

# Set up parameters
nome_mes = "Maio"
ano_sel = 2026
mes_sel = 5

p_mes = pd.Period(f"{ano_sel}-{mes_sel:02d}", freq='M')
p_90 = [p_mes - 2, p_mes - 1, p_mes]

dt_vd_devol_inicio_str = (p_mes - 2).start_time.strftime("%Y-%m-%d")
dt_vd_devol_fim_str = p_mes.end_time.strftime("%Y-%m-%d")

df_vd = fetch_all("""
    SELECT valor_total, quantidade, custo_frete_rateado, comissao_valor, custo_acordos_rede, custo_descarga, custo_cmv_real, data
    FROM vendas
    WHERE status = 'FATURADO' AND data >= ? AND data <= ?
""", (dt_vd_devol_inicio_str, dt_vd_devol_fim_str))

print("=== Raw df_vd ===")
print(df_vd)

df_vd['data'] = pd.to_datetime(df_vd['data'], errors='coerce')
df_vd['sale_month'] = df_vd['data'].dt.to_period('M')

print("\n=== Datatypes ===")
print("p_mes type:", type(p_mes), "value:", p_mes)
print("sale_month series type:", df_vd['sale_month'].dtype)
print("sale_month elements type:", type(df_vd['sale_month'].iloc[0]))

print("\n=== Filtering ===")
mask = df_vd['sale_month'] == p_mes
print("Mask:")
print(mask)
df_vd_mes = df_vd[mask]
print("Filtered df_vd_mes:")
print(df_vd_mes)
print("Sum:", df_vd_mes['valor_total'].sum())
