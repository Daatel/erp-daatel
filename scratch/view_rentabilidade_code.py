import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\12_Rentabilidade_Cliente.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(90, min(len(lines), 130)):
    print(f"{idx+1}: {lines[idx].strip()}")
