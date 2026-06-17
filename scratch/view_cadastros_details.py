import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\1_Cadastros.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_lines(start, end):
    print(f"=== Lines {start} to {end} ===")
    for idx in range(start-1, min(len(lines), end)):
        print(f"{idx+1}: {lines[idx].strip()}")

print_lines(490, 535)
print_lines(589, 650)
