from database import fetch_all

email = 'admin@alho.com'
senha = 'admin123'

df = fetch_all("SELECT id, nome, nivel_permissao FROM usuarios WHERE email=? AND senha=? AND status='ATIVO'", (email, senha))
print("Login result:")
print(df.to_string())
