"""
seed_fichas_tecnicas.py — Fichas Tecnicas com perda ZERO na receita.
A perda real e declarada pelo operador no apontamento do lote de producao.
"""
import sqlite3

conn = sqlite3.connect("erp_fabrica.db")
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

def get_id(nome_parcial):
    cur.execute("SELECT id, nome FROM produtos WHERE nome LIKE ?", (f"%{nome_parcial}%",))
    rows = cur.fetchall()
    if not rows:
        raise ValueError(f"Produto nao encontrado: '{nome_parcial}'")
    if len(rows) > 1:
        raise ValueError(f"Multiplos encontrados para '{nome_parcial}': {rows}")
    return rows[0][0], rows[0][1]

pf_1kg_id,   pf_1kg_nome   = get_id("Alho Descascado Premium In Natura 1kg")
pf_500g_id,  pf_500g_nome  = get_id("Alho Descascado Premium In Natura 500g")
mp_alho_id,  mp_alho_nome  = get_id("Alho In Natura (Sujo)")
emb_1kg_id,  emb_1kg_nome  = get_id("Saco Plastico 1kg")
emb_500g_id, emb_500g_nome = get_id("Saco Plastico 500g")

print(f"  PF 1kg  : ID {pf_1kg_id}  | {pf_1kg_nome}")
print(f"  PF 500g : ID {pf_500g_id} | {pf_500g_nome}")
print(f"  MP      : ID {mp_alho_id} | {mp_alho_nome}")
print(f"  Emb 1kg : ID {emb_1kg_id} | {emb_1kg_nome}")
print(f"  Emb 500g: ID {emb_500g_id}| {emb_500g_nome}")
print()

# Remove fichas anteriores se existirem
for pid in (pf_1kg_id, pf_500g_id):
    cur.execute("SELECT id FROM fichas_tecnicas WHERE produto_id=?", (pid,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM fichas_tecnicas_itens WHERE ficha_id=?", (row[0],))
        cur.execute("DELETE FROM fichas_tecnicas WHERE id=?", (row[0],))

# ── FICHA: Alho Descascado 1kg ───────────────────────────────────────────────
# Receita: 1 KG de MP + 1 saco plástico → 1 SACO de 1kg
# Perda zero na ficha. Perda real declarada na producao.
cur.execute(
    "INSERT INTO fichas_tecnicas (produto_id, rendimento_percentual, observacoes) VALUES (?,?,?)",
    (pf_1kg_id, 100.0, "1,0 kg alho sujo + 1 saco 1kg. Perda real declarada no lote.")
)
ficha_1kg_id = cur.lastrowid
cur.executemany(
    "INSERT INTO fichas_tecnicas_itens (ficha_id, insumo_id, quantidade_por_unidade, tipo) VALUES (?,?,?,?)",
    [
        (ficha_1kg_id, mp_alho_id,  1.0, "MP"),
        (ficha_1kg_id, emb_1kg_id,  1.0, "EMBALAGEM"),
    ]
)
print(f"  [OK] {pf_1kg_nome}")
print(f"       MP : 1,0000 KG  | {mp_alho_nome}")
print(f"       EMB: 1 UN       | {emb_1kg_nome}")

# ── FICHA: Alho Descascado 500g ──────────────────────────────────────────────
# Receita: 0,5 KG de MP + 1 saco plástico → 1 SACO de 500g
# Perda zero na ficha. Perda real declarada na producao.
cur.execute(
    "INSERT INTO fichas_tecnicas (produto_id, rendimento_percentual, observacoes) VALUES (?,?,?)",
    (pf_500g_id, 100.0, "0,5 kg alho sujo + 1 saco 500g. Perda real declarada no lote.")
)
ficha_500g_id = cur.lastrowid
cur.executemany(
    "INSERT INTO fichas_tecnicas_itens (ficha_id, insumo_id, quantidade_por_unidade, tipo) VALUES (?,?,?,?)",
    [
        (ficha_500g_id, mp_alho_id,  0.5, "MP"),
        (ficha_500g_id, emb_500g_id, 1.0, "EMBALAGEM"),
    ]
)
print(f"  [OK] {pf_500g_nome}")
print(f"       MP : 0,5000 KG  | {mp_alho_nome}")
print(f"       EMB: 1 UN       | {emb_500g_nome}")

conn.commit()
conn.close()

print()
print("=" * 55)
print("  FICHAS TECNICAS CRIADAS (perda zero na receita)")
print()
print("  Alho Descascado 1kg  (1 SACO):")
print("    1,0 KG Alho In Natura + 1 Saco Plastico 1kg")
print()
print("  Alho Descascado 500g (1 SACO):")
print("    0,5 KG Alho In Natura + 1 Saco Plastico 500g")
print()
print("  Perda real -> declarada no modulo Producao.")
print("=" * 55)
