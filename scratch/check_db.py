import database
conn = database.get_connection()
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'funcionarios'")
print("Funcionários Columns:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'rh_pagamentos'")
print("Pagamentos Columns:", [r[0] for r in cur.fetchall()])
