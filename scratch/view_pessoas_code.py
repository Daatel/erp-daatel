import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\3_Pessoas.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(990, min(len(lines), 1050)):
    print(f"{idx+1}: {lines[idx].strip()}")
