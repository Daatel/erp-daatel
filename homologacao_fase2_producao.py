"""
homologacao_fase2_producao.py
Fase 2 do drill: apontamento de 2 lotes de producao usando as Fichas Tecnicas.

LOTE 1 — Alho Descascado 1kg
  Produto: Alho Descascado Premium In Natura 1kg
  Volume:  500 sacos de 1kg
  Insumos (Ficha Tecnica):
    - Alho In Natura (Sujo): 500 KG  (500 sacos x 1,0 KG/saco)
    - Saco Plastico 1kg    : 500 UN  (500 sacos x 1 saco/unidade)
  Perda real declarada: 60 KG (cascas/sujeira — ~12%)
  Horario: 07:00 – 16:00 (9h de maquina)

LOTE 2 — Alho Descascado 500g
  Produto: Alho Descascado Premium In Natura 500g
  Volume:  600 sacos de 500g
  Insumos (Ficha Tecnica):
    - Alho In Natura (Sujo): 300 KG  (600 sacos x 0,5 KG/saco)
    - Saco Plastico 500g   : 600 UN  (600 sacos x 1 saco/unidade)
  Perda real declarada: 30 KG (~10%)
  Horario: 07:00 – 14:00 (7h de maquina)
"""

import sqlite3
from datetime import date, datetime, timedelta

DB    = "erp_fabrica.db"
TODAY = date.today()

CUSTO_FIXO_MENSAL = 20_000.0  # R$ igual ao configurado na UI
DIAS_UTEIS_MES    = 21
HORAS_DIA_PADRAO  = 8.0

def custo_hora():
    return (CUSTO_FIXO_MENSAL / DIAS_UTEIS_MES) / HORAS_DIA_PADRAO

def dur_horas(hi_str, hf_str):
    hi = datetime.strptime(hi_str, "%H:%M")
    hf = datetime.strptime(hf_str, "%H:%M")
    d  = (hf - hi).total_seconds() / 3600
    return d + 24 if d < 0 else d

def get_id(cur, table, col, val):
    cur.execute(f"SELECT id FROM {table} WHERE {col} LIKE ?", (f"%{val}%",))
    r = cur.fetchone()
    if not r: raise ValueError(f"Nao encontrado em {table}.{col}: '{val}'")
    return r[0]

def get_custo(cur, produto_id):
    cur.execute("SELECT custo_unidade FROM produtos WHERE id=?", (produto_id,))
    r = cur.fetchone()
    return float(r[0] or 0.0) if r else 0.0

def registrar_lote(
    cur, data, hora_ini, hora_fim,
    produto_id, produto_nome,
    qtd_produzida,              # unidades do PF geradas
    perdas_kg,
    data_validade,
    insumos,                    # lista de dicts: produto_id, nome, qtd_puxada, sobra
    observacoes=""
):
    """
    insumos: [{'produto_id': int, 'nome': str, 'qtd_puxada': float, 'sobra': float}]
    qtd_consumida = qtd_puxada - sobra  (calculado aqui)
    """
    # 1. Calculo de custo MP
    custo_mp = 0.0
    for ins in insumos:
        qt_c    = ins['qtd_puxada'] - ins['sobra']
        ins['qtd_consumida'] = qt_c
        c_unit  = get_custo(cur, ins['produto_id'])
        ins['custo_unit'] = c_unit
        custo_mp += qt_c * c_unit

    # 2. Overhead de maquina
    horas       = dur_horas(hora_ini, hora_fim)
    overhead    = custo_hora() * horas

    # 3. Custo total e unitario
    custo_total = custo_mp + overhead
    custo_unit  = custo_total / qtd_produzida

    # 4. Cabecalho do Lote (producao_diaria)
    peso_principal = insumos[0]['qtd_consumida'] if insumos else 0.0
    obs_sobras = " | ".join(
        [f"Puxado: {i['qtd_puxada']}kg, Sobrou: {i['sobra']}kg de {i['nome']}"
         for i in insumos if i['sobra'] > 0]
    )
    obs_final = observacoes
    if obs_sobras:
        obs_final = f"{observacoes}\n[Auditoria de Sobras]: {obs_sobras}".strip()

    cur.execute("""
        INSERT INTO producao_diaria
            (data, hora_inicio, hora_fim, materia_prima_kg, produto_id,
             produto_final_kg, perdas_kg, observacoes,
             custo_total_lote, custo_unitario_lote, data_validade)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.strftime("%Y-%m-%d"), hora_ini, hora_fim,
        peso_principal, produto_id, qtd_produzida, perdas_kg,
        obs_final, custo_total, custo_unit,
        data_validade.strftime("%Y-%m-%d")
    ))
    lote_id = cur.lastrowid
    ref     = f"Lote OP #{lote_id}"

    # 5. Insumos: baixa no estoque e registro na producao_insumos
    for ins in insumos:
        pid   = ins['produto_id']
        qt_p  = ins['qtd_puxada']
        sob   = ins['sobra']
        qt_c  = ins['qtd_consumida']

        # Registro para DRE
        cur.execute(
            "INSERT INTO producao_insumos (producao_id, produto_id, quantidade) VALUES (?,?,?)",
            (lote_id, pid, qt_c)
        )
        # Saida do estoque (tudo que foi puxado)
        cur.execute("""
            INSERT INTO estoque_movimentos
                (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia)
            VALUES (?,?,'Saída',?,?,?)
        """, (data.strftime("%Y-%m-%d"), pid, qt_p, "Producao_Requisicao", ref))

        # Devolucao da sobra
        if sob > 0:
            cur.execute("""
                INSERT INTO estoque_movimentos
                    (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia)
                VALUES (?,?,'Entrada',?,?,?)
            """, (data.strftime("%Y-%m-%d"), pid, sob, "Producao_Devolucao_Sobra", ref))

    # 6. Entrada do Produto Acabado no Estoque
    cur.execute("""
        INSERT INTO estoque_movimentos
            (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia)
        VALUES (?,?,'Entrada',?,?,?)
    """, (data.strftime("%Y-%m-%d"), produto_id, qtd_produzida, "Producao_Entrada", ref))

    # 7. Atualiza custo do produto acabado
    cur.execute("UPDATE produtos SET custo_unidade=? WHERE id=?", (custo_unit, produto_id))

    return lote_id, custo_mp, overhead, custo_total, custo_unit, horas


# ══════════════════════════════════════════════════════════════════════════════

print("=" * 64)
print("  FASE 2 — PRODUCAO | ERP Fabrica de Alho")
print("  Data:", TODAY.strftime("%d/%m/%Y"))
print("=" * 64)

c   = sqlite3.connect(DB)
c.execute("PRAGMA foreign_keys = ON")
cur = c.cursor()

# IDs
prod_alho1kg  = get_id(cur, "produtos", "nome", "Alho Descascado Premium In Natura 1kg")
prod_alho500g = get_id(cur, "produtos", "nome", "Alho Descascado Premium In Natura 500g")
mp_alho       = get_id(cur, "produtos", "nome", "Alho In Natura (Sujo)")
emb_saco1kg   = get_id(cur, "produtos", "nome", "Saco Plastico 1kg")
emb_saco500g  = get_id(cur, "produtos", "nome", "Saco Plastico 500g")

print(f"\n  PF 1kg={prod_alho1kg} | PF 500g={prod_alho500g}")
print(f"  MP Alho={mp_alho} | Saco1kg={emb_saco1kg} | Saco500g={emb_saco500g}")
print(f"  Custo/hora overhead: R${custo_hora():.4f}")

# ─── LOTE 1: 500 sacos de Alho Descascado 1kg ─────────────────────────────
print("\n" + "─"*64)
print("  LOTE 1 — Alho Descascado Premium In Natura 1kg")
print("  Volume: 500 sacos | 07:00-16:00 (9h) | Perda: 60 KG")

lote1_id, mp1, oh1, ct1, cu1, h1 = registrar_lote(
    cur,
    data           = TODAY,
    hora_ini       = "07:00",
    hora_fim       = "16:00",
    produto_id     = prod_alho1kg,
    produto_nome   = "Alho Descascado Premium In Natura 1kg",
    qtd_produzida  = 500.0,
    perdas_kg      = 60.0,
    data_validade  = TODAY + timedelta(days=90),
    insumos=[
        {'produto_id': mp_alho,     'nome': "Alho In Natura (Sujo)",
         'qtd_puxada': 560.0,  'sobra': 0.0},   # 500 consumido + 60 de perda
        {'produto_id': emb_saco1kg, 'nome': "Saco Plastico 1kg",
         'qtd_puxada': 500.0,  'sobra': 0.0},   # 500 sacos exatos
    ],
    observacoes = "Homologacao Lote 1 — Alho Descascado 1kg"
)
print(f"  [OK] Lote #{lote1_id}")
print(f"       Duracao: {h1:.1f}h | Overhead: R${oh1:.2f}")
print(f"       Custo MP: R${mp1:.2f} | Custo Total: R${ct1:.2f}")
print(f"       Custo Unitario: R${cu1:.4f}/saco")
print(f"       Margem bruta: R${20.50 - cu1:.4f}/saco ({((20.50-cu1)/20.50*100):.1f}%)")

# ─── LOTE 2: 600 sacos de Alho Descascado 500g ────────────────────────────
print("\n" + "─"*64)
print("  LOTE 2 — Alho Descascado Premium In Natura 500g")
print("  Volume: 600 sacos | 07:00-14:00 (7h) | Perda: 30 KG")

lote2_id, mp2, oh2, ct2, cu2, h2 = registrar_lote(
    cur,
    data           = TODAY,
    hora_ini       = "07:00",
    hora_fim       = "14:00",
    produto_id     = prod_alho500g,
    produto_nome   = "Alho Descascado Premium In Natura 500g",
    qtd_produzida  = 600.0,
    perdas_kg      = 30.0,
    data_validade  = TODAY + timedelta(days=90),
    insumos=[
        {'produto_id': mp_alho,      'nome': "Alho In Natura (Sujo)",
         'qtd_puxada': 330.0,  'sobra': 0.0},   # 300 consumido + 30 de perda
        {'produto_id': emb_saco500g, 'nome': "Saco Plastico 500g",
         'qtd_puxada': 600.0,  'sobra': 0.0},   # 600 sacos exatos
    ],
    observacoes = "Homologacao Lote 2 — Alho Descascado 500g"
)
print(f"  [OK] Lote #{lote2_id}")
print(f"       Duracao: {h2:.1f}h | Overhead: R${oh2:.2f}")
print(f"       Custo MP: R${mp2:.2f} | Custo Total: R${ct2:.2f}")
print(f"       Custo Unitario: R${cu2:.4f}/saco")
print(f"       Margem bruta: R${10.25 - cu2:.4f}/saco ({((10.25-cu2)/10.25*100):.1f}%)")

c.commit()

# ─── VERIFICACAO DE ESTOQUE POS-PRODUCAO ──────────────────────────────────
print("\n" + "─"*64)
print("  ESTOQUE POS-PRODUCAO:")
cur.execute("""
    SELECT p.nome, p.unidade_medida,
           SUM(CASE WHEN em.tipo_movimento='Entrada' THEN em.quantidade
                    WHEN em.tipo_movimento='Saida'   THEN -em.quantidade
                    WHEN em.tipo_movimento='Saída'   THEN -em.quantidade
                    ELSE 0 END) as saldo
    FROM estoque_movimentos em
    JOIN produtos p ON em.produto_id = p.id
    GROUP BY em.produto_id
    ORDER BY p.nome
""")
for nome, unid, saldo in cur.fetchall():
    flag = " ✅" if saldo >= 0 else " ⚠️ NEGATIVO"
    print(f"  {nome:45s}  {saldo:>10.2f} {unid}{flag}")

c.close()

print("\n" + "=" * 64)
print("  FASE 2 CONCLUIDA!")
print()
print("  RESUMO DOS LOTES:")
print(f"  Lote #{lote1_id}: 500 sacos Alho 1kg  | R${cu1:.4f}/un | Margem {((20.50-cu1)/20.50*100):.1f}%")
print(f"  Lote #{lote2_id}: 600 sacos Alho 500g | R${cu2:.4f}/un | Margem {((10.25-cu2)/10.25*100):.1f}%")
print()
print("  Proximo passo: homologacao_fase3_vendas.py")
print("=" * 64)
