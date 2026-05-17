from database import fetch_all

df = fetch_all("SELECT id, nivel_permissao FROM usuarios")
for idx, row in df.iterrows():
    print(f"ID {row['id']}: {repr(row['nivel_permissao'])}")
