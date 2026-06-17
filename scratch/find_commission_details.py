import os

def search_details(filepath):
    print(f"=== {os.path.basename(filepath)} ===")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            if any(x in line.lower() for x in ["comissao", "comissão", "comissões"]):
                print(f"{idx+1}: {line.strip()}")
    except Exception as e:
        print(f"Error: {e}")

search_details(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\9_Financeiro.py")
search_details(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\3_Pessoas.py")
search_details(r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages\7_Faturamento.py")
