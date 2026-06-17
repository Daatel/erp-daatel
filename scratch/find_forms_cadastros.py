import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\1_Cadastros.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    line_lower = line.lower()
    if "st.form(" in line_lower or "st.expander(" in line_lower:
        print(f"{idx+1}: {line.strip()}")
