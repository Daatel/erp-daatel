import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\3_Pessoas.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    line_lower = line.lower()
    if "st.form(" in line_lower or "chave_pix" in line_lower or "dados_bancarios" in line_lower:
        print(f"{idx+1}: {line.strip()}")
