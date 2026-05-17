"""
homologacao_fase3_5.py
Fases 3, 4 e 5 do drill de homologacao:

FASE 3 — Pedidos de Venda (3 pedidos)
  PED-01: Agrofruti       — 200 sacos Alho 1kg   @ R$20,50  = R$4.100,00  prazo 7d
  PED-02: Superm. Mundial — 100 sacos Alho 1kg   @ R$20,50  = R$2.050,00  prazo 30d
           + taxa descarga R$150
  PED-03: Sacolao Silva   — 300 sacos Alho 500g  @ R$10,25  = R$3.075,00  prazo 28d

FASE 4 — Faturamento (todos os 3 pedidos → NF)
  Baixa de estoque + gera Contas a Receber

FASE 5 — Liquidacao Financeira
  Paga os 2 boletos de compra (Fazenda + Plasticos)
  Recebe os 3 titulos de venda
  Verifica saldo final das contas bancarias
"""

import sqlite3
from datetime import date, timedelta

DB    = "erp_fabrica.db"
TODAY = date.today()

def get_conn():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys = ON")
    return c

def q(conn, sql, params=()):
    conn.execute(sql, params)

def fetch(conn, sql, params=()):
    cur = conn.execute(sql, params)
    return cur.fetchall()

def get_id(conn, table, col, val):
    r = fetch(conn, f"SELECT id FROM {table} WHERE {col} LIKE ?", (f"%{val}%",))
    if not r: raise ValueError(f"Nao encontrado: {table}.{col} LIKE '%{val}%'")
    return r[0][0]

def fmt(v): return f"R${v:>10.2f}"


print("=" * 64)
print("  FASES 3-4-5 — VENDAS + FATURAMENTO + FINANCEIRO")
print("  Data:", TODAY.strftime("%d/%m/%Y"))
print("=" * 64)

conn = get_conn()

# ── IDs dos atores ─────────────────────────────────────────────────────────
cli_agro    = get_id(conn, "clientes",     "nome", "Agrofruti")
cli_mundial = get_id(conn, "clientes",     "nome", "Mundial")
cli_silva   = get_id(conn, "clientes",     "nome", "Silva")
vend_id     = fetch(conn, "SELECT id FROM funcionarios LIMIT 1")[0][0]   # qualquer vendedor

prod_1kg    = get_id(conn, "produtos",     "nome", "In Natura 1kg")
prod_500g   = get_id(conn, "produtos",     "nome", "In Natura 500g")

pc_receita  = fetch(conn, "SELECT id FROM planos_de_contas WHERE categoria LIKE '%Receita%' LIMIT 1")
pc_receita_id = pc_receita[0][0] if pc_receita else None

banco_itau  = get_id(conn, "contas_bancarias", "nome", "Ita")   # Itaú Principal

print(f"\n  Clientes: Agro={cli_agro}, Mundial={cli_mundial}, Silva={cli_silva}")
print(f"  Produtos: 1kg={prod_1kg}, 500g={prod_500g}")
print(f"  PC Receita={pc_receita_id} | Banco Itaú={banco_itau}")

# ══════════════════════════════════════════════════════════════════════════════
# FASE 3 — PEDIDOS DE VENDA
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*64)
print("  FASE 3 — PEDIDOS DE VENDA")

pedidos = [
    # (cliente_id, vendedor_id, produto_id, qtd, preco_unit, descricao)
    (cli_agro,    vend_id, prod_1kg,  200, 20.50, "Agrofruti - Alho 1kg"),
    (cli_mundial, vend_id, prod_1kg,  100, 20.50, "Superm. Mundial - Alho 1kg"),
    (cli_silva,   vend_id, prod_500g, 300, 10.25, "Sacolao Silva - Alho 500g"),
]

venda_ids = []
for cli_id, vend, prod_id, qtd, preco, desc in pedidos:
    v_total = qtd * preco
    q(conn, """
        INSERT INTO vendas
            (data, cliente_id, vendedor_id, produto_id, quantidade,
             valor_unitario, valor_total, comissao_valor, custo_acordos_rede, status)
        VALUES (?,?,?,?,?,?,?,?,?,'APROVADO')
    """, (TODAY.strftime("%Y-%m-%d"), cli_id, vend, prod_id, qtd,
          preco, v_total, 0.0, 0.0))
    vid = fetch(conn, "SELECT MAX(id) FROM vendas")[0][0]
    venda_ids.append(vid)
    print(f"  [OK] Pedido #{vid}: {desc:40s} {qtd:4d} un × {fmt(preco)} = {fmt(v_total)}")

conn.commit()

# ══════════════════════════════════════════════════════════════════════════════
# FASE 4 — FATURAMENTO (todos os 3 pedidos)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*64)
print("  FASE 4 — FATURAMENTO (NF)")

# Prazos dos clientes
prazos = {
    cli_agro:    7,
    cli_mundial: 30,
    cli_silva:   28,
}

# Taxa de descarga do Mundial = R$150
taxa_descarga_mundial = 150.0

for vid in venda_ids:
    row = fetch(conn, """
        SELECT v.cliente_id, v.produto_id, v.quantidade, v.valor_total,
               c.nome, p.nome
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.id=?
    """, (vid,))[0]
    cli_id, prod_id, qtd, v_total, cli_nome, prod_nome = row

    # 1. Muda status da venda
    q(conn, "UPDATE vendas SET status='FATURADO', tipo_documento='Nota Fiscal (NF)' WHERE id=?", (vid,))

    # 2. Baixa de estoque (Saida)
    q(conn, """
        INSERT INTO estoque_movimentos
            (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia)
        VALUES (?,?,'Saída',?,?,?)
    """, (TODAY.strftime("%Y-%m-%d"), prod_id, qtd,
          "Expedicao Nota Fiscal (NF)", f"Venda #{vid}"))

    # 3. Conta a Receber
    prazo = prazos.get(cli_id, 30)
    venc  = (TODAY + timedelta(days=prazo)).strftime("%Y-%m-%d")
    desc_fin = f"NF - Venda #{vid} ({cli_nome} - {prod_nome})"
    q(conn, """
        INSERT INTO contas_a_receber
            (venda_id, cliente_id, plano_conta_id, descricao, valor, data_vencimento, status)
        VALUES (?,?,?,?,?,?,'PENDENTE')
    """, (vid, cli_id, pc_receita_id, desc_fin, v_total, venc))
    car_id = fetch(conn, "SELECT MAX(id) FROM contas_a_receber")[0][0]

    # 4. Taxa de descarga (só Mundial)
    taxa = taxa_descarga_mundial if cli_id == cli_mundial else 0.0
    if taxa > 0:
        q(conn, "UPDATE vendas SET custo_descarga=? WHERE id=?", (taxa, vid))
        desc_taxa = f"Taxa Descarga CD - {cli_nome} - Venda #{vid}"
        q(conn, """
            INSERT INTO contas_a_pagar
                (plano_conta_id, descricao, valor, data_vencimento, status)
            VALUES (?,?,?,?,'PENDENTE')
        """, (None, desc_taxa, taxa, TODAY.strftime("%Y-%m-%d")))

    print(f"  [OK] Faturado Venda #{vid}: {cli_nome:25s} | {fmt(v_total)} | venc {venc} | CAR#{car_id}")

conn.commit()

# ══════════════════════════════════════════════════════════════════════════════
# FASE 5 — LIQUIDACAO FINANCEIRA
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─"*64)
print("  FASE 5 — LIQUIDACAO FINANCEIRA")

# Saldo antes
saldo_antes = fetch(conn, "SELECT saldo_inicial FROM contas_bancarias WHERE id=?", (banco_itau,))[0][0]
mov_antes   = fetch(conn, "SELECT COALESCE(SUM(CASE WHEN tipo='Entrada' THEN valor ELSE -valor END),0) FROM fluxo_caixa WHERE conta_bancaria_id=?", (banco_itau,))[0][0]
saldo_atual = saldo_antes + mov_antes
print(f"\n  Saldo Itaú antes das liquidacoes: {fmt(saldo_atual)}")

def liquidar_cap(conn, cap_id, banco_id, data_pag, desc):
    """Liquida uma conta a pagar."""
    row = fetch(conn, "SELECT valor FROM contas_a_pagar WHERE id=?", (cap_id,))
    if not row: raise ValueError(f"CAP #{cap_id} nao encontrado")
    valor = row[0][0]
    q(conn, "UPDATE contas_a_pagar SET status='PAGO', data_pagamento=? WHERE id=?",
      (data_pag, cap_id))
    q(conn, """
        INSERT INTO fluxo_caixa (data, tipo, categoria, valor, descricao, conta_bancaria_id)
        VALUES (?,'Saída','Pagamento Fornecedor',?,?,?)
    """, (data_pag, valor, desc, banco_id))
    return valor

def liquidar_car(conn, car_id, banco_id, data_rec, desc):
    """Liquida uma conta a receber."""
    row = fetch(conn, "SELECT valor FROM contas_a_receber WHERE id=?", (car_id,))
    if not row: raise ValueError(f"CAR #{car_id} nao encontrado")
    valor = row[0][0]
    q(conn, "UPDATE contas_a_receber SET status='RECEBIDO', data_recebimento=? WHERE id=?",
      (data_rec, car_id))
    q(conn, """
        INSERT INTO fluxo_caixa (data, tipo, categoria, valor, descricao, conta_bancaria_id)
        VALUES (?,'Entrada','Recebimento de Venda',?,?,?)
    """, (data_rec, valor, desc, banco_id))
    return valor

data_pag = TODAY.strftime("%Y-%m-%d")

# Paga os 2 boletos de compra (IDs 1 e 2 gerados na Fase 1)
caps = fetch(conn, "SELECT id, descricao, valor FROM contas_a_pagar WHERE status='PENDENTE' ORDER BY id")
print()
total_pago = 0.0
for cap_id, desc, valor in caps:
    if cap_id in (1, 2):   # Boletos das compras NF-001 e NF-002
        v = liquidar_cap(conn, cap_id, banco_itau, data_pag, desc)
        print(f"  [PAGO]    CAP #{cap_id}: {desc[:50]:50s} {fmt(v)}")
        total_pago += v

# Recebe os 3 titulos de venda
cars = fetch(conn, "SELECT id, descricao, valor FROM contas_a_receber WHERE status='PENDENTE' ORDER BY id")
print()
total_recebido = 0.0
for car_id, desc, valor in cars:
    v = liquidar_car(conn, car_id, banco_itau, data_pag, desc)
    print(f"  [RECEBIDO] CAR #{car_id}: {desc[:48]:48s} {fmt(v)}")
    total_recebido += v

conn.commit()

# Saldo final
mov_depois = fetch(conn, "SELECT COALESCE(SUM(CASE WHEN tipo='Entrada' THEN valor ELSE -valor END),0) FROM fluxo_caixa WHERE conta_bancaria_id=?", (banco_itau,))[0][0]
saldo_final = saldo_antes + mov_depois

print()
print("─"*64)
print(f"  Saldo Itaú ANTES     : {fmt(saldo_atual)}")
print(f"  (-) Total Pago       : {fmt(total_pago)}")
print(f"  (+) Total Recebido   : {fmt(total_recebido)}")
print(f"  Saldo Itaú DEPOIS    : {fmt(saldo_final)}")

# ── Estoque final ────────────────────────────────────────────────────────────
print("\n" + "─"*64)
print("  ESTOQUE FINAL (pos-vendas):")
rows = fetch(conn, """
    SELECT p.nome,
           SUM(CASE WHEN em.tipo_movimento='Entrada' THEN em.quantidade
                    ELSE -em.quantidade END) as saldo
    FROM estoque_movimentos em
    JOIN produtos p ON em.produto_id = p.id
    GROUP BY em.produto_id
    ORDER BY p.nome
""")
for nome, saldo in rows:
    flag = " ✅" if saldo >= 0 else " ⚠️ NEGATIVO"
    print(f"  {nome:45s}  {saldo:>10.2f}{flag}")

conn.close()

print()
print("=" * 64)
print("  FASES 3-4-5 CONCLUIDAS!")
print()
print("  RESUMO FINANCEIRO:")
print(f"  Receita bruta de vendas : {fmt(total_recebido)}")
print(f"  Pagamentos a fornecedores: {fmt(total_pago)}")
print(f"  Resultado liquido caixa : {fmt(total_recebido - total_pago)}")
print()
print("  Proximo passo: verificar DRE no modulo 10_DRE.py")
print("=" * 64)
