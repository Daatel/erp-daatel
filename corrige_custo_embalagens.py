"""
Corrige o custo_unidade dos sacos plasticos:
  O sistema gravou o preco do MILHEIRO (R$80) como custo unitario.
  Custo real por UN = preco_por_milheiro / 1.000
  Saco 1kg : R$80  / 1.000 = R$0,0800/un
  Saco 500g: R$70  / 1.000 = R$0,0700/un
Em seguida refaz o calculo de custo dos 2 lotes de producao.
"""
import sqlite3
from datetime import date, datetime

DB    = "erp_fabrica.db"
TODAY = date.today()

CUSTO_FIXO_MENSAL = 20_000.0
DIAS_UTEIS_MES    = 21
HORAS_DIA_PADRAO  = 8.0

def custo_hora():
    return (CUSTO_FIXO_MENSAL / DIAS_UTEIS_MES) / HORAS_DIA_PADRAO

def dur_horas(hi_str, hf_str):
    hi = datetime.strptime(hi_str, "%H:%M")
    hf = datetime.strptime(hf_str, "%H:%M")
    d  = (hf - hi).total_seconds() / 3600
    return d + 24 if d < 0 else d

c   = sqlite3.connect(DB)
c.execute("PRAGMA foreign_keys = ON")
cur = c.cursor()

# ─── 1. Corrige custo_unidade dos sacos ───────────────────────────────────
# Saco 1kg: comprado a R$80/MILHEIRO → custo unitario = R$0,0800
# Saco 500g: comprado a R$70/MILHEIRO → custo unitario = R$0,0700
cur.execute("UPDATE produtos SET custo_unidade=? WHERE nome LIKE '%Saco Plastico 1kg%'",  (80.0/1000,))
cur.execute("UPDATE produtos SET custo_unidade=? WHERE nome LIKE '%Saco Plastico 500g%'", (70.0/1000,))
print("  [OK] Custo unitario corrigido:")
cur.execute("SELECT nome, custo_unidade FROM produtos WHERE nome LIKE '%Saco%'")
for nome, cu in cur.fetchall():
    print(f"       {nome}: R${cu:.6f}/UN")

# ─── 2. Recalcula custo dos lotes 1 e 2 ───────────────────────────────────
def recalcular_lote(lote_id, produto_id, qtd_produzida, hora_ini, hora_fim):
    # Busca insumos do lote
    cur.execute("""
        SELECT pi.produto_id, pi.quantidade, p.custo_unidade, p.nome
        FROM producao_insumos pi
        JOIN produtos p ON pi.produto_id = p.id
        WHERE pi.producao_id = ?
    """, (lote_id,))
    insumos = cur.fetchall()

    custo_mp = sum(qtd * cu for _, qtd, cu, _ in insumos)
    horas    = dur_horas(hora_ini, hora_fim)
    overhead = custo_hora() * horas
    custo_total = custo_mp + overhead
    custo_unit  = custo_total / qtd_produzida

    cur.execute(
        "UPDATE producao_diaria SET custo_total_lote=?, custo_unitario_lote=? WHERE id=?",
        (custo_total, custo_unit, lote_id)
    )
    cur.execute("UPDATE produtos SET custo_unidade=? WHERE id=?", (custo_unit, produto_id))
    return custo_mp, overhead, custo_total, custo_unit, insumos

print()
print("─" * 64)
print("  RECALCULO LOTE #1 — Alho Descascado 1kg (500 sacos, 9h)")

pf_1kg  = cur.execute("SELECT id FROM produtos WHERE nome LIKE '%In Natura 1kg%'").fetchone()[0]
pf_500g = cur.execute("SELECT id FROM produtos WHERE nome LIKE '%In Natura 500g%'").fetchone()[0]

mp1, oh1, ct1, cu1, ins1 = recalcular_lote(1, pf_1kg,  500.0, "07:00", "16:00")
print(f"  Insumos consumidos:")
for pid, qtd, cu, nome in ins1:
    print(f"    {nome:40s}  {qtd:8.2f} un × R${cu:.6f} = R${qtd*cu:8.4f}")
print(f"  Custo MP     : R${mp1:>10.4f}")
print(f"  Overhead (9h): R${oh1:>10.4f}")
print(f"  Custo Total  : R${ct1:>10.4f}")
print(f"  Custo Unit.  : R${cu1:>10.4f}/saco")
print(f"  Preco Venda  : R${20.50:>10.4f}/saco")
print(f"  Margem Bruta : R${20.50-cu1:>10.4f}/saco  ({((20.50-cu1)/20.50*100):.1f}%)")

print()
print("─" * 64)
print("  RECALCULO LOTE #2 — Alho Descascado 500g (600 sacos, 7h)")
mp2, oh2, ct2, cu2, ins2 = recalcular_lote(2, pf_500g, 600.0, "07:00", "14:00")
print(f"  Insumos consumidos:")
for pid, qtd, cu, nome in ins2:
    print(f"    {nome:40s}  {qtd:8.2f} un × R${cu:.6f} = R${qtd*cu:8.4f}")
print(f"  Custo MP     : R${mp2:>10.4f}")
print(f"  Overhead (7h): R${oh2:>10.4f}")
print(f"  Custo Total  : R${ct2:>10.4f}")
print(f"  Custo Unit.  : R${cu2:>10.4f}/saco")
print(f"  Preco Venda  : R${10.25:>10.4f}/saco")
print(f"  Margem Bruta : R${10.25-cu2:>10.4f}/saco  ({((10.25-cu2)/10.25*100):.1f}%)")

c.commit()
c.close()

print()
print("=" * 64)
print("  CUSTOS CORRIGIDOS!")
print(f"  Lote #1  500 sacos 1kg   custo R${cu1:.4f}  margem {((20.50-cu1)/20.50*100):.1f}%")
print(f"  Lote #2  600 sacos 500g  custo R${cu2:.4f}  margem {((10.25-cu2)/10.25*100):.1f}%")
print("=" * 64)
