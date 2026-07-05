import sys
sys.path.append('c:/Users/MARCIO/Gestao_Fabrica_Alho')
from database import initialize_database, fetch_all

print("Initializing database...")
initialize_database()

print("Fetching clients table details...")
df = fetch_all("PRAGMA table_info(clientes)")
print(df)
