import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\3_Pessoas.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if any(x in line.lower() for x in ["comissao", "comissão", "comissões"]):
        print(f"{idx+1}: {line.strip()}")
