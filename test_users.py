from database import fetch_all

df = fetch_all("SELECT * FROM usuarios")
print("All users:")
print(df.to_string())
