with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\1_Cadastros.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    line_lower = line.lower()
    if any(x in line_lower for x in ["insert into clientes", "update clientes", "insert into fornecedores", "update fornecedores"]):
        print(f"{idx+1}: {line.strip()}")
