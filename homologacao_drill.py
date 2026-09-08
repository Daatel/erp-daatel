"""
homologacao_drill.py
Executa o drill de homologacao end-to-end via Python direto no banco.
Replica exatamente a logica do modulo Compras (UI), Producao e Vendas.

FASE 1 — Compras + Estoque + Contas a Pagar
  NF-001: Alho In Natura  (Fazenda Sao Jose)   1.000 KG  @ R$12,00
  NF-002: Sacos Plasticos (Plasticos SA)        2 MILH 1kg + 3 MILH 500g
"""

import sqlite3
from datetime import date, timedelta

DB = "erp_fabrica.db"
TODAY = date.today()

def conn():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys = ON")
    return c

def get_id(cur, table, col, val):
    cur.execute(f"SELECT id FROM {table} WHERE {col} LIKE ?", (f"%{val}%",))
    r = cur.fetchone()
    if not r: raise ValueError(f"Nao encontrado em {table}.{col}: '{val}'")
    return r[0]

def get_prazo(cur, fornecedor_id):
    cur.execute("SELECT prazo_pagamento FROM fornecedores WHERE id=?", (fornecedor_id,))
    r = cur.fetchone()
    return r[0] if r else "30"

def parse_prazo(prazo_str):
    """Converte '28' ou '30/60' em lista de dias."""
    if not prazo_str or prazo_str.strip().lower() in ("a vista","avista","0"):
        return [0]
    partes = [p.strip() for p in prazo_str.replace(","," ").replace("/"," ").split()]
    try:
        return [int(p) for p in partes if p.isdigit()]
    except:
        return [30]

def registrar_compra(
    cur, fornecedor_id, tipo_doc, numero_doc, data_compra,
    itens, plano_id=None, obs=""
):
    """
    itens = lista de dicts:
      produto_id, produto_nome, destino ('PRODUCAO'|'REVENDA'),
      unidade, quantidade (na unidade de compra),
      qtd_estoque (em UN — ja convertida),
      preco_bruto_unit, icms=0, ipi=0
    """
    total_bruto = sum(it['preco_bruto_unit'] * it['quantidade'] for it in itens)
    destinos_str = ", ".join(set(it['destino'] for it in itens))

    # 1. Cabecalho da Compra
    cur.execute("""
        INSERT INTO compras
            (fornecedor_id, data_compra, tipo_insumo, valor_total,
             tipo_doc, numero_doc, observacoes)
        VALUES (?,?,?,?,?,?,?)
    """, (fornecedor_id, data_compra.strftime("%Y-%m-%d"), destinos_str,
          total_bruto, tipo_doc, numero_doc, obs))
    compra_id = cur.lastrowid

    for it in itens:
        icms = it.get('icms', 0.0)
        ipi  = it.get('ipi',  0.0)
        custo_liq = (it['preco_bruto_unit'] * it['quantidade'] - icms - ipi) / it['quantidade']
        total_liq = custo_liq * it['quantidade']

        # 2. Item da NF
        cur.execute("""
            INSERT INTO compras_itens
                (compra_id, produto_id, produto_nome, destino, unidade,
                 quantidade, quantidade_estoque,
                 preco_unitario_bruto, icms_valor, ipi_valor,
                 custo_unitario_liquido, total_liquido_item)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (compra_id, it['produto_id'], it['produto_nome'], it['destino'],
              it['unidade'], it['quantidade'], it['qtd_estoque'],
              it['preco_bruto_unit'], icms, ipi, custo_liq, total_liq))

        # 3. Movimento de Estoque
        if it['destino'] in ('PRODUCAO', 'REVENDA'):
            cur.execute("""
                INSERT INTO estoque_movimentos
                    (data, produto_id, tipo_movimento, quantidade, origem)
                VALUES (?, ?, 'Entrada', ?, ?)
            """, (data_compra.strftime("%Y-%m-%d"), it['produto_id'],
                  it['qtd_estoque'],
                  f"Compra {tipo_doc} {numero_doc} (ID #{compra_id})"))

            # 4. Atualiza custo unitario no cadastro (preço unitário de estoque)
            custo_medio_unidade = total_liq / it['qtd_estoque'] if it['qtd_estoque'] > 0 else custo_liq
            cur.execute("UPDATE produtos SET custo_unidade=? WHERE id=?",
                        (custo_medio_unidade, it['produto_id']))

    # 5. Duplicatas (Contas a Pagar)
    prazo_str = get_prazo(cur, fornecedor_id)
    dias_list = parse_prazo(prazo_str)
    n = len(dias_list)
    valor_p = round(total_bruto / n, 2)
    diff_p  = round(total_bruto - valor_p * n, 2)
    parc_ids = []
    for i, dias in enumerate(dias_list):
        v = valor_p + (diff_p if i == n-1 else 0)
        d = (data_compra + timedelta(days=dias)).strftime("%Y-%m-%d")
        desc = f"{tipo_doc} {numero_doc}/{i+1} | forn#{fornecedor_id}"
        cur.execute("""
            INSERT INTO contas_a_pagar
                (compra_id, fornecedor_id, plano_conta_id, descricao,
                 valor, data_vencimento, status)
            VALUES (?,?,?,?,?,?,'PENDENTE')
        """, (compra_id, fornecedor_id, plano_id, desc, v, d))
        parc_ids.append(cur.lastrowid)

    return compra_id, total_bruto, parc_ids

# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("  DRILL DE HOMOLOGACAO — ERP Fabrica de Alho")
print("  Data:", TODAY.strftime("%d/%m/%Y"))
print("=" * 60)

c = conn()
cur = c.cursor()

# ─── IDs dos atores ────────────────────────────────────────────────────────
forn_fazenda = get_id(cur, "fornecedores", "nome", "Fazenda")
forn_plastico = get_id(cur, "fornecedores", "nome", "Pl")  # 'Plásticos SA'

prod_alho     = get_id(cur, "produtos", "nome", "Alho In Natura")
prod_saco1kg  = get_id(cur, "produtos", "nome", "Saco Plastico 1kg")
prod_saco500  = get_id(cur, "produtos", "nome", "Saco Plastico 500g")

print(f"\n  Fornecedores: Fazenda={forn_fazenda}, Plasticos={forn_plastico}")
print(f"  Produtos: AlhoMP={prod_alho}, Saco1kg={prod_saco1kg}, Saco500g={prod_saco500}")

# ──────────────────────────────────────────────────────────────────────────────
# COMPRA #1 — NF-001: Alho In Natura  1.000 KG @ R$12,00
# Fornecedor: Fazenda Sao Jose do Alho | Prazo: 30 dias
# Total Bruto: R$12.000,00 | 1 duplicata de R$12.000,00
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "─"*60)
print("  COMPRA #1 — NF-001 | Fazenda Sao Jose do Alho")
compra1_id, total1, parc1 = registrar_compra(
    cur,
    fornecedor_id = forn_fazenda,
    tipo_doc      = "NF",
    numero_doc    = "NF-001",
    data_compra   = TODAY,
    itens=[{
        'produto_id':     prod_alho,
        'produto_nome':   "Alho In Natura (Sujo)",
        'destino':        "PRODUCAO",
        'unidade':        "KG",
        'quantidade':     1000.0,    # 1.000 KG comprados
        'qtd_estoque':    1000.0,    # 1.000 KG entram no estoque (sem conversao)
        'preco_bruto_unit': 12.00,
    }],
)
print(f"  [OK] Compra ID #{compra1_id} | Total: R${total1:,.2f}")
print(f"       {len(parc1)} duplicata(s) geradas: IDs {parc1}")

# ──────────────────────────────────────────────────────────────────────────────
# COMPRA #2 — NF-002: Embalagens Plasticas
# Saco Plastico 1kg : 2 MILHEIRO × 1.000 = 2.000 UN | R$80,00/MILH
# Saco Plastico 500g: 3 MILHEIRO × 1.000 = 3.000 UN | R$70,00/MILH
# Fornecedor: Plasticos SA | Prazo: 28 dias
# Total Bruto: 2×80 + 3×70 = 160+210 = R$370,00
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "─"*60)
print("  COMPRA #2 — NF-002 | Plasticos SA")
compra2_id, total2, parc2 = registrar_compra(
    cur,
    fornecedor_id = forn_plastico,
    tipo_doc      = "NF",
    numero_doc    = "NF-002",
    data_compra   = TODAY,
    itens=[
        {
            'produto_id':     prod_saco1kg,
            'produto_nome':   "Saco Plastico 1kg",
            'destino':        "REVENDA",
            'unidade':        "MILHEIRO",
            'quantidade':     2.0,       # 2 MILHEIROS comprados
            'qtd_estoque':    2000.0,    # 2 x 1.000 UN entram no estoque
            'preco_bruto_unit': 80.00,   # R$80 por MILHEIRO
        },
        {
            'produto_id':     prod_saco500,
            'produto_nome':   "Saco Plastico 500g",
            'destino':        "REVENDA",
            'unidade':        "MILHEIRO",
            'quantidade':     3.0,       # 3 MILHEIROS
            'qtd_estoque':    3000.0,    # 3 x 1.000 UN entram no estoque
            'preco_bruto_unit': 70.00,   # R$70 por MILHEIRO
        },
    ],
)
print(f"  [OK] Compra ID #{compra2_id} | Total: R${total2:,.2f}")
print(f"       {len(parc2)} duplicata(s) geradas: IDs {parc2}")

c.commit()

# ──────────────────────────────────────────────────────────────────────────────
# VERIFICACAO DE ESTOQUE
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "─"*60)
print("  VERIFICACAO DE ESTOQUE APÓS COMPRAS:")
cur.execute("""
    SELECT p.nome, p.unidade_medida, SUM(
        CASE WHEN em.tipo_movimento='Entrada' THEN em.quantidade
             WHEN em.tipo_movimento='Saída'   THEN -em.quantidade
             ELSE 0 END) as saldo
    FROM estoque_movimentos em
    JOIN produtos p ON em.produto_id = p.id
    GROUP BY em.produto_id
    ORDER BY p.nome
""")
rows = cur.fetchall()
for nome, unid, saldo in rows:
    print(f"  {nome:40s}  {saldo:>10.2f} {unid}")

# ──────────────────────────────────────────────────────────────────────────────
# VERIFICACAO CONTAS A PAGAR
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "─"*60)
print("  CONTAS A PAGAR GERADAS:")
cur.execute("""
    SELECT COALESCE(f.nome_fantasia, f.nome), cap.descricao, cap.valor,
           cap.data_vencimento, cap.status
    FROM contas_a_pagar cap
    JOIN fornecedores f ON cap.fornecedor_id = f.id
    ORDER BY cap.id
""")
rows = cur.fetchall()
total_cap = 0
for fant, desc, valor, venc, status in rows:
    print(f"  {fant:20s} | {desc:35s} | R${valor:>9.2f} | {venc} | {status}")
    total_cap += valor
print(f"  {'TOTAL A PAGAR':>60s} | R${total_cap:>9.2f}")

c.close()
print("\n" + "=" * 60)
print("  FASE 1 CONCLUIDA COM SUCESSO!")
print("  Proximos passos:")
print("  - Verificar no Streamlit: Compras, Estoque, Financeiro")
print("  - Executar homologacao_fase2.py (Producao)")
print("=" * 60)
