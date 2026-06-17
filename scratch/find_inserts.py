import os

with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\database.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = re.finditer(r"(INSERT INTO contas_a_pagar|contas_a_pagar)", content, re.IGNORECASE)
for m in matches:
    start = max(0, m.start() - 100)
    end = min(len(content), m.end() + 200)
    print(f"--- MATCH ---")
    print(content[start:end])
