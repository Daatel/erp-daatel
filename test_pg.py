from database import fetch_all
import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        df = fetch_all("SELECT * FROM produtos LIMIT 1")
        print(df)
        print("Success!")
except Exception as e:
    print(f"Error: {e}")
