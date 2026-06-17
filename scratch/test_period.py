import pandas as pd

p_mes = pd.Period("2026-06", freq='M')
print("p_mes:", p_mes)
print("p_mes - 2 start:", (p_mes - 2).start_time.strftime("%Y-%m-%d"))
print("p_mes + 1 end:", (p_mes + 1).end_time.strftime("%Y-%m-%d"))
print("p_mes end:", p_mes.end_time.strftime("%Y-%m-%d"))

p_90 = [p_mes - 2, p_mes - 1, p_mes]
print("p_90:", p_90)
