import os

keywords = ["comissao_valor", "comissao", "comissões", "comissão"]
pages_dir = r"C:\Users\MARCIO\Gestao_Fabrica_Alho\pages"

for file in os.listdir(pages_dir):
    if file.endswith(".py"):
        filepath = os.path.join(pages_dir, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                for kw in keywords:
                    if kw in content:
                        print(f"Found '{kw}' in {file}")
        except Exception as e:
            print(f"Error reading {file}: {e}")
