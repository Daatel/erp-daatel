import sqlite3

conn = sqlite3.connect('erp_fabrica.db')
cur = conn.cursor()

# Saco Plastico: unidade de compra = MILHEIRO, fator = 1000 (ja correto no seed)
# Corrige unidade_medida para MILHEIRO (assim o form de Compras mostra MILHEIRO como unidade padrao)
cur.execute("UPDATE produtos SET unidade_medida='MILHEIRO' WHERE nome LIKE 'Saco Pl%'")

# Verifica todos os produtos
cur.execute("SELECT nome, unidade_medida, unidades_por_fardo, is_materia_prima FROM produtos ORDER BY id")
rows = cur.fetchall()
print("\nPRODUTOS CADASTRADOS:")
print("-" * 70)
for r in rows:
    tipo = "MP" if r[3] else "EMB/PF"
    print(f"  {r[0]:42s} | {tipo:6s} | unid: {r[1]:12s} | fator conv: {r[2]}")

conn.commit()
conn.close()
print("\n[OK] Unidades dos sacos plasticos corrigidas para MILHEIRO.")
