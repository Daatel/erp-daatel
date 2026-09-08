import sqlite3
c = sqlite3.connect('erp_fabrica.db')
for t in ['producao_insumos','producao_diaria','compras_itens','compras',
          'estoque_movimentos','contas_a_pagar','contas_a_receber','fluxo_caixa']:
    c.execute(f'DELETE FROM {t}')
    try:
        c.execute(f"UPDATE sqlite_sequence SET seq=0 WHERE name='{t}'")
    except: pass
c.commit()
c.close()
print("Limpeza OK — banco zerado para nova tentativa")
