import sqlite3
conn = sqlite3.connect('C:/Users/MARCIO/Gestao_Fabrica_Alho/erp_fabrica.db')
c = conn.cursor()
try:
    c.execute("ALTER TABLE funcionarios ADD COLUMN status TEXT DEFAULT 'ATIVO'")
except Exception as e:
    print(e)
try:
    c.execute("ALTER TABLE funcionarios ADD COLUMN data_termino DATE")
except Exception as e:
    print(e)
conn.commit()
conn.close()
print('OK')
