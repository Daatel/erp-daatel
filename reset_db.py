"""
reset_db.py — Reset TOTAL do banco de dados ERP Fábrica de Alho
Apaga TODOS os dados e re-semeia os cadastros base para o drill de homologação.

Regras de negócio embutidas no seed:
  - Saco Plástico: comprado em MILHEIRO (1 milh = 1.000 UN), consumido em UN
  - 2 SKUs de produto final: Alho Descascado Premium 1kg e 500g
  - Alho Descascado 500g é o mais vendido (preço unitário configurado adequadamente)
"""

import sqlite3
import os
from datetime import date

DB_NAME = "erp_fabrica.db"

# ─────────────────────────────────────────────
# 1. TABELAS TRANSACIONAIS — apagar na ordem
#    certa (FK deps: filhos antes dos pais)
# ─────────────────────────────────────────────
TABELAS_TRANSACIONAIS = [
    "producao_insumos",
    "producao_diaria",
    "compras_itens",
    "compras_materia_prima",
    "compras",
    "contas_a_pagar",
    "contas_a_receber",
    "estoque_movimentos",
    "vendas",
    "manifestos_carga",
    "fluxo_caixa",
    "rh_pagamentos",
    "devolucoes",
    "tabelas_preco",
]

# ─────────────────────────────────────────────
# 2. CADASTROS BASE — apagar E re-semear
# ─────────────────────────────────────────────
TABELAS_CADASTROS = [
    "comissoes_regras",
    "funcionarios",
    "clientes",
    "fornecedores",
    "produtos",
    "redes_clientes",
    "grupos_clientes",
    "planos_de_contas",
    "contas_bancarias",
    "maquinario",
    "usuarios",
]

def reset_and_seed():
    if not os.path.exists(DB_NAME):
        print(f"[ERRO] Banco '{DB_NAME}' não encontrado. Execute na pasta do projeto.")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    print("=" * 55)
    print("  RESET TOTAL - ERP Fabrica de Alho")
    print("=" * 55)

    # ── Apaga tudo ───────────────────────────
    todas = TABELAS_TRANSACIONAIS + TABELAS_CADASTROS
    for t in todas:
        cur.execute(f"DELETE FROM {t}")
        print(f"  [OK] Limpou: {t}")

    # Zera auto-increment
    cur.execute("DELETE FROM sqlite_sequence")
    conn.commit()
    print("\n  Sequencias resetadas.\n")

    # ═════════════════════════════════════════
    # SEED — CONTAS BANCÁRIAS
    # ═════════════════════════════════════════
    cur.executemany(
        """INSERT INTO contas_bancarias
           (nome, banco, agencia, conta, saldo_inicial, tipo_conta, status)
           VALUES (?,?,?,?,?,?,?)""",
        [
            ("Conta Itaú Principal", "Itaú",  "0001", "12345-6", 50000.0, "Corrente", "ATIVO"),
            ("Conta Bradesco Reserva", "Bradesco", "0042", "98765-4", 15000.0, "Corrente", "ATIVO"),
        ]
    )
    print("  ✓ Contas bancárias inseridas")

    # ═════════════════════════════════════════
    # SEED — PLANOS DE CONTAS
    # ═════════════════════════════════════════
    cur.executemany(
        "INSERT INTO planos_de_contas (categoria, nome) VALUES (?,?)",
        [
            # Receitas
            ("RECEITA",    "Venda de Produtos"),
            ("RECEITA",    "Venda de Subprodutos"),
            # CMV / Custo Variável
            ("CMV",        "Custo da Mercadoria Vendida"),
            ("CMV",        "Custo da Embalagem"),
            # Compras / Entradas
            ("COMPRA",     "Compra de Matéria-Prima"),
            ("COMPRA",     "Compra de Embalagens"),
            ("COMPRA",     "Compra de Insumos"),
            # Despesas Operacionais
            ("DESPESA_OP", "Frete e Logística"),
            ("DESPESA_OP", "Manutenção de Equipamentos"),
            ("DESPESA_OP", "Energia Elétrica"),
            ("DESPESA_OP", "Aluguel"),
            # RH
            ("RH",         "Salários e Encargos"),
            ("RH",         "Comissões de Vendas"),
            # Acordos Comerciais
            ("ACORDOS",    "Taxa de Descarga"),
            ("ACORDOS",    "Acordo Logístico / Rebate de Rede"),
            ("ACORDOS",    "Contrato Comercial"),
        ]
    )
    print("  ✓ Planos de contas inseridos")

    # ═════════════════════════════════════════
    # SEED — FORNECEDORES
    # ═════════════════════════════════════════
    cur.executemany(
        """INSERT INTO fornecedores
           (nome, telefone, cnpj_cpf, cidade, uf, plano_de_contas, status, prazo_pagamento)
           VALUES (?,?,?,?,?,?,?,?)""",
        [
            ("Fazenda São José do Alho",  "(62) 99800-0001", "12.345.678/0001-90",
             "Senador Canedo", "GO", "Compra de Matéria-Prima", "ATIVO", "30 dias"),
            ("Plásticos SA",              "(11) 3344-5566",  "23.456.789/0001-01",
             "São Paulo",      "SP", "Compra de Embalagens",    "ATIVO", "28 dias"),
            ("Transportadora Rápida Ltda","(62) 3322-1100",  "34.567.890/0001-12",
             "Goiânia",        "GO", "Frete e Logística",       "ATIVO", "15 dias"),
            ("Manutenção Industrial GO",  "(62) 98877-6655", "45.678.901/0001-23",
             "Aparecida de Goiânia", "GO", "Manutenção de Equipamentos", "ATIVO", "À Vista"),
        ]
    )
    print("  ✓ Fornecedores inseridos")

    # ═════════════════════════════════════════
    # SEED — REDES E GRUPOS DE CLIENTES
    # ═════════════════════════════════════════
    cur.execute("INSERT INTO redes_clientes (nome) VALUES (?)", ("VAREJO INDEPENDENTE",))
    cur.execute("INSERT INTO redes_clientes (nome) VALUES (?)", ("SUPERMERCADOS",))
    conn.commit()
    cur.execute("SELECT id FROM redes_clientes WHERE nome='VAREJO INDEPENDENTE'")
    rede_var = cur.fetchone()[0]
    cur.execute("SELECT id FROM redes_clientes WHERE nome='SUPERMERCADOS'")
    rede_super = cur.fetchone()[0]

    cur.executemany(
        "INSERT INTO grupos_clientes (rede_id, nome) VALUES (?,?)",
        [
            (rede_var,   "Sacolão / Feira"),
            (rede_super, "Supermercado Regional"),
        ]
    )
    print("  ✓ Redes e grupos de clientes inseridos")

    # ═════════════════════════════════════════
    # SEED — CLIENTES
    #   Agrofruti  → prazo 7d  (DAV)
    #   Mundial    → prazo 30d (NF)
    #   Silva      → prazo 28d (NF)
    # ═════════════════════════════════════════
    cur.executemany(
        """INSERT INTO clientes
           (nome, nome_fantasia, telefone, cnpj_cpf, cidade, uf,
            prazo_pagamento, prazo_pagamento_dias,
            rede_clientes, taxa_descarga, status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        [
            ("Agrofruti Comércio Ltda", "Agrofruti",
             "(62) 3211-4400", "56.789.012/0001-34",
             "Goiânia", "GO",
             "7 dias", 7,
             "VAREJO INDEPENDENTE", 0.0, "ATIVO"),

            ("Supermercados Mundial S/A", "Supermercados Mundial",
             "(62) 3500-7000", "67.890.123/0001-45",
             "Goiânia", "GO",
             "30 dias", 30,
             "SUPERMERCADOS", 150.0, "ATIVO"),   # taxa descarga R$150

            ("Sacolão do Silva ME", "Sacolão do Silva",
             "(62) 99123-4567", "78.901.234/0001-56",
             "Aparecida de Goiânia", "GO",
             "28 dias", 28,
             "VAREJO INDEPENDENTE", 0.0, "ATIVO"),
        ]
    )
    print("  ✓ Clientes inseridos")

    # ═════════════════════════════════════════
    # SEED — FUNCIONÁRIOS (1 vendedor)
    # ═════════════════════════════════════════
    cur.execute(
        """INSERT INTO funcionarios
           (nome, cargo, salario_base, regime_contratacao,
            data_admissao, gatilho_comissao, status)
           VALUES (?,?,?,?,?,?,?)""",
        ("João Vendedor", "Representante Comercial", 1500.0,
         "PJ", "2024-01-02", "FATURAMENTO", "ATIVO")
    )
    print("  ✓ Funcionários inseridos")

    # ═════════════════════════════════════════
    # SEED — PRODUTOS
    #
    # Fonte: Tabela de Preços — Empório do Alho II Ltda
    #
    # MATÉRIAS-PRIMAS:
    #   Alho In Natura (Sujo) — KG
    #   Óleo Vegetal           — L
    #   Sal de Cozinha         — KG
    #   Pimenta Vermelha       — KG
    #   Mix de Ervas Secas     — KG
    #
    # EMBALAGENS (compradas em MILHEIRO, consumidas em UN):
    #   Saco Plástico 1kg      — MILHEIRO × 1.000
    #   Saco Plástico 500g     — MILHEIRO × 1.000
    #   Saco Plástico 80g      — MILHEIRO × 1.000
    #   Caixa 220g (Tempero)   — CX (1 UN = 1 CX)
    #
    # PRODUTOS FINAIS (8 SKUs da tabela oficial):
    #   REF 1 — Alho Descascado Premium In Natura 1kg
    #   REF 4 — Alho Descascado Premium In Natura 500g
    #   REF 7 — Alho Frito 1kg
    #   REF 8 — Alho Frito 500g
    #   REF 6 — Tempero Alho e Sal 220g
    #   REF 3 — Tempero Completo com Ervas 220g
    #   REF 2 — Tempero Completo com Pimenta 220g
    #   REF 5 — Alho Frito 80g
    # ═════════════════════════════════════════
    cur.executemany(
        """INSERT INTO produtos
           (nome, unidade_medida, preco_venda_base, is_materia_prima,
            marca, peso_volume, referencia, ean,
            tipo_embalagem, unidades_por_fardo,
            custo_unidade, custo_fardo, estoque_minimo)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [
            # ── MATÉRIAS-PRIMAS ──────────────────────────────────────────────
            # nome                       unid   preco  MP    marca   peso   ref   ean    tip_emb  fardo  custo  cfardo  min
            ("Alho In Natura (Sujo)",    "KG",  0.0,   1,    None,   "KG",  None, None,  None,    None,  0.0,   0.0,    500.0),
            ("Oleo Vegetal",             "L",   0.0,   1,    None,   "L",   None, None,  None,    None,  0.0,   0.0,    20.0),
            ("Sal de Cozinha",           "KG",  0.0,   1,    None,   "KG",  None, None,  None,    None,  0.0,   0.0,    50.0),
            ("Pimenta Vermelha",         "KG",  0.0,   1,    None,   "KG",  None, None,  None,    None,  0.0,   0.0,    10.0),
            ("Mix de Ervas Secas",       "KG",  0.0,   1,    None,   "KG",  None, None,  None,    None,  0.0,   0.0,    10.0),

            # ── EMBALAGENS (unid_medida = MILHEIRO, fator 1000 → UN) ─────────
            ("Saco Plastico 1kg",        "MILHEIRO", 0.0, 0, None,  "1kg", None, None,  "SACO",  1000,  0.0,   0.0,    1.0),
            ("Saco Plastico 500g",       "MILHEIRO", 0.0, 0, None, "500g", None, None,  "SACO",  1000,  0.0,   0.0,    1.0),
            ("Saco Plastico 80g",        "MILHEIRO", 0.0, 0, None,  "80g", None, None,  "SACO",  1000,  0.0,   0.0,    1.0),
            ("Caixa Tempero 220g",       "CX",  0.0,   0,    None, "220g", None, None,  "CAIXA", 1,     0.0,   0.0,    1.0),

            # ── PRODUTOS FINAIS (8 SKUs) ──────────────────────────────────────
            # Alho Descascado In Natura 1kg — REF 1 — EAN 7898880650058 — 10/fardo SACO
            ("Alho Descascado Premium In Natura 1kg",
             "SACO", 20.50, 0, "EMPORIO ALHO", "1 Kg", "1", "789888065058", "SACO", 10, 0.0, 205.00, 50.0),

            # Alho Descascado In Natura 500g — REF 4 — EAN 789888065010 — 20/fardo SACO
            ("Alho Descascado Premium In Natura 500g",
             "SACO", 10.25, 0, "EMPORIO ALHO", "500 g", "4", "789888065010", "SACO", 20, 0.0, 205.00, 100.0),

            # Alho Frito 1kg — REF 7 — EAN 789888413002 — 10/fardo SACO
            ("Alho Frito 1kg",
             "SACO", 24.99, 0, "EMPORIO ALHO", "1 Kg", "7", "789888413002", "SACO", 10, 0.0, 249.90, 30.0),

            # Alho Frito 500g — REF 8 — EAN 789888413019 — 15/fardo SACO
            ("Alho Frito 500g",
             "SACO", 12.99, 0, "EMPORIO ALHO", "500 g", "8", "789888413019", "SACO", 15, 0.0, 194.85, 50.0),

            # Tempero Alho e Sal 220g — REF 6 — EAN 6314309534491 — 12/cx CAIXA
            ("Tempero Alho e Sal 220g",
             "CX", 2.49, 0, "EMPORIO ALHO", "220 g", "6", "6314309534491", "CAIXA", 12, 0.0, 29.88, 100.0),

            # Tempero Completo com Ervas 220g — REF 3 — EAN 789888065034 — 12/cx CAIXA
            ("Tempero Completo com Ervas 220g",
             "CX", 2.49, 0, "EMPORIO ALHO", "220 g", "3", "789888065034", "CAIXA", 12, 0.0, 29.88, 100.0),

            # Tempero Completo com Pimenta 220g — REF 2 — EAN 789888065027 — 12/cx CAIXA
            ("Tempero Completo com Pimenta 220g",
             "CX", 2.49, 0, "EMPORIO ALHO", "220 g", "2", "789888065027", "CAIXA", 12, 0.0, 29.88, 100.0),

            # Alho Frito 80g — REF 5 — EAN 789888065041 — 12/cx CAIXA
            ("Alho Frito 80g",
             "CX", 4.99, 0, "EMPORIO ALHO", "80 g", "5", "789888065041", "CAIXA", 12, 0.0, 59.88, 100.0),
        ]
    )
    print("  [OK] Materias-primas: 5 (Alho Sujo, Oleo, Sal, Pimenta, Ervas)")
    print("  [OK] Embalagens: 4 (Saco 1kg/500g/80g em MILHEIRO, Caixa 220g)")
    print("  [OK] Produtos Finais: 8 SKUs (tabela oficial Emporio do Alho)")
    print("    REF1 Alho Descascado 1kg     R$20,50/SACO  | 10 SACOS/fardo")
    print("    REF4 Alho Descascado 500g    R$10,25/SACO  | 20 SACOS/fardo")
    print("    REF7 Alho Frito 1kg          R$24,99/SACO  | 10 SACOS/fardo")
    print("    REF8 Alho Frito 500g         R$12,99/SACO  | 15 SACOS/fardo")
    print("    REF6 Tempero Alho e Sal 220g  R$2,49/CX    | 12 CX/caixa")
    print("    REF3 Tempero c/ Ervas 220g    R$2,49/CX    | 12 CX/caixa")
    print("    REF2 Tempero c/ Pimenta 220g  R$2,49/CX    | 12 CX/caixa")
    print("    REF5 Alho Frito 80g           R$4,99/CX    | 12 CX/caixa")

    # ═════════════════════════════════════════
    # SEED — MAQUINÁRIO
    # ═════════════════════════════════════════
    cur.executemany(
        """INSERT INTO maquinario
           (nome, valor_aquisicao, vida_util_anos,
            valor_depreciacao_mensal, data_aquisicao, status)
           VALUES (?,?,?,?,?,?)""",
        [
            ("Descascadeira Industrial HS-500", 45000.0, 10, 375.0, "2023-03-15", "ATIVO"),
            ("Câmara Fria 20m³",               30000.0,  15, 166.67, "2022-07-01", "ATIVO"),
            ("Balança Industrial 500kg",         8000.0,   8,  83.33, "2023-01-10", "ATIVO"),
            ("Seladora a Vácuo",                12000.0,  10, 100.0, "2023-06-20", "ATIVO"),
        ]
    )
    print("  ✓ Maquinário inserido")

    # ═════════════════════════════════════════
    # SEED — USUÁRIO ADMIN
    # ═════════════════════════════════════════
    cur.execute(
        """INSERT INTO usuarios (nome, email, senha, nivel_permissao, status)
           VALUES (?,?,?,?,?)""",
        ("Administrador", "admin@fabrica.com", "admin123", "ADMIN", "ATIVO")
    )
    print("  ✓ Usuário admin inserido")

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    print()
    print("=" * 55)
    print("  ✅  RESET CONCLUÍDO COM SUCESSO!")
    print()
    print("  CADASTROS BASE PRONTOS PARA HOMOLOGAÇÃO:")
    print("  ─────────────────────────────────────────")
    print("  💰 Contas Bancárias:")
    print("     • Itaú Principal     R$ 50.000,00")
    print("     • Bradesco Reserva   R$ 15.000,00")
    print()
    print("  🏭 Fornecedores (4):")
    print("     • Fazenda São José do Alho  (30d)")
    print("     • Plásticos SA              (28d)")
    print("     • Transportadora Rápida     (15d)")
    print("     • Manutenção Industrial GO  (À Vista)")
    print()
    print("  🛒 Clientes (3):")
    print("     • Agrofruti          7d  | taxa descarga: R$0")
    print("     • Supermercados Mundial 30d | taxa descarga: R$150")
    print("     • Sacolão do Silva   28d | taxa descarga: R$0")
    print()
    print("  📦 Produtos (5 SKUs):")
    print("     • Alho In Natura (Sujo)           MP / KG")
    print("     • Saco Plástico 1kg     EMB / UN (compra: MILHEIRO)")
    print("     • Saco Plástico 500g    EMB / UN (compra: MILHEIRO)")
    print("     • Alho Descascado Premium 1kg   R$ 28,00")
    print("     • Alho Descascado Premium 500g  R$ 15,50  ← mais vendido")
    print("=" * 55)


if __name__ == "__main__":
    reset_and_seed()
