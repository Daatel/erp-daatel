with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\12_Rentabilidade_Cliente.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if any(x in line.lower() for x in ["contas_a_pagar", "contas_a_receber", "despesa", "vencimento"]):
        print(f"{idx+1}: {line.strip()}")
