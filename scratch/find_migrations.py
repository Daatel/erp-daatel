with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\database.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "alter table" in line.lower() or "migration" in line.lower() or "update_database" in line.lower() or "check_column" in line.lower():
        print(f"{idx+1}: {line.strip()}")
