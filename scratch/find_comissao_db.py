with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\database.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "comissao" in line.lower() or "comissão" in line.lower():
        print(f"{idx+1}: {line.strip()}")
