# Spec Técnica v2: Modo de Estoque (SIMPLIFICADO/LOTE)

> **Contexto para o agente:** ERP em Python/Streamlit (Gestão Fábrica de Alho), banco SQLite/PostgreSQL, **single-tenant**. A Parte 1 (bugfix do `st.rerun()` dentro de `db_transaction`) já foi implementada e commitada em `main` — não repetir. Esta spec v2 cobre apenas o switch de modo de estoque, com nomes de tabela confirmados contra o schema real e dois ajustes de revisão técnica incorporados.

---

## Motivação (sem alteração)

Cliente está em Fase 1 de implantação (financeiro/comercial). Controle de estoque por lote/FIFO ainda não tem disciplina operacional de captura, gerando warnings de "Estoque Negativo" e CMV "estimado" em todo faturamento — ruído que corrói confiança do usuário na fase mais sensível da implantação.

## Decisão de design (sem alteração)

Switch de configuração com dois modos:
- `SIMPLIFICADO`: CMV calculado por custo cadastrado no produto (sem lote físico, sem warning de estoque negativo).
- `LOTE`: comportamento atual (FIFO por lote), para Fase 2+.

Movimentação de estoque (quantidade) continua sendo registrada em `estoque_movimentos` em ambos os modos, sem bloqueio por saldo negativo quando em `SIMPLIFICADO`. O que muda é apenas o cálculo de CMV e a supressão de alertas de natureza operacional (estoque/lote) — alertas de natureza cadastral (custo ausente, ver Ajuste B) permanecem ativos em qualquer modo.

---

## 1. Schema: configuração — sem tenant_id

```sql
CREATE TABLE IF NOT EXISTS configuracoes_sistema (
    chave   VARCHAR(50) PRIMARY KEY,
    valor   VARCHAR(50) NOT NULL
);

INSERT INTO configuracoes_sistema (chave, valor)
VALUES ('modo_estoque', 'SIMPLIFICADO')
ON CONFLICT (chave) DO NOTHING;  -- ajustar sintaxe para SQLite: usar INSERT OR IGNORE
```

> Se já existir uma tabela genérica de configuração no projeto (ex: `empresa_config`), avaliar reuso. Caso `empresa_config` seja estruturada para um registro único de dados cadastrais da empresa (não chave-valor), manter `configuracoes_sistema` como tabela separada, dedicada a flags/configurações operacionais.

## 2. Schema: cadastro de produto — custo médio

```sql
ALTER TABLE produtos ADD COLUMN IF NOT EXISTS custo_medio NUMERIC(12,2) DEFAULT 0;
```

`custo_unidade` (já existente, custo padrão de cadastro) passa a servir de **fallback** — ver Ajuste B.

## 3. Schema: rastreabilidade do método de CMV

```sql
ALTER TABLE vendas ADD COLUMN IF NOT EXISTS cmv_metodo VARCHAR(20) DEFAULT 'LOTE';
```

`vendas` já possui `custo_cmv_real` — nenhuma coluna nova de valor é necessária, apenas `cmv_metodo` para marcar qual lógica gerou aquele valor.

---

## 4. Função central de decisão (com Ajuste B: fallback + alerta de cadastro)

```python
def get_config(chave: str, conn, default: str = None) -> str:
    """Busca uma configuração do sistema. Retorna default se não encontrada."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT valor FROM configuracoes_sistema WHERE chave = %s" if is_pg else
        "SELECT valor FROM configuracoes_sistema WHERE chave = ?",
        (chave,)
    )
    row = cursor.fetchone()
    return row[0] if row else default


def calcular_cmv(produto_id: int, quantidade: float, conn) -> dict:
    """
    Retorna {
        'valor': float,
        'metodo': 'SIMPLIFICADO' | 'LOTE',
        'custo_ausente': bool,  # True só é possível em modo SIMPLIFICADO
    }
    """
    modo = get_config("modo_estoque", conn, default="LOTE")

    if modo == "SIMPLIFICADO":
        valor, custo_ausente = calcular_cmv_por_custo_medio(produto_id, quantidade, conn)
        return {"valor": valor, "metodo": "SIMPLIFICADO", "custo_ausente": custo_ausente}
    else:
        valor = calcular_cmv_por_lote_fifo(produto_id, quantidade, conn)  # função já existente, inalterada
        return {"valor": valor, "metodo": "LOTE", "custo_ausente": False}


def calcular_cmv_por_custo_medio(produto_id: int, quantidade: float, conn) -> tuple[float, bool]:
    """
    Usa custo_medio; se ausente/zero, faz fallback para custo_unidade (custo de cadastro).
    Retorna (valor_cmv, custo_ausente) — custo_ausente=True se nenhum dos dois estiver preenchido,
    sinalizando problema de CADASTRO (não de estoque/lote).
    """
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COALESCE(custo_medio, 0.0), COALESCE(custo_unidade, 0.0)
           FROM produtos WHERE id = %s""" if is_pg else
        """SELECT COALESCE(custo_medio, 0.0), COALESCE(custo_unidade, 0.0)
           FROM produtos WHERE id = ?""",
        (produto_id,)
    )
    row = cursor.fetchone()
    custo_medio = float(row[0]) if row else 0.0
    custo_unidade = float(row[1]) if row else 0.0

    custo_final = custo_medio if custo_medio > 0.0 else custo_unidade
    custo_ausente = custo_final == 0.0

    return custo_final * quantidade, custo_ausente
```

A função `calcular_cmv_por_lote_fifo` existente permanece **inalterada**.

## 5. Ajuste no fluxo de faturamento (`pages/7_Faturamento.py`)

```python
alertas_custo_ausente = []  # acumula para exibir agrupado, não um warning por iteração solto

for _, row in pedidos_selecionados.iterrows():
    resultado_cmv = calcular_cmv(row['produto_id'], row['quantidade'], conn)

    # grava em vendas: custo_cmv_real = resultado_cmv['valor'], cmv_metodo = resultado_cmv['metodo']

    if resultado_cmv["custo_ausente"]:
        alertas_custo_ausente.append(row.get('produto_nome', row['produto_id']))

    # movimentação de estoque: sempre registrada, independente do modo
    registrar_movimentacao_estoque(
        produto_id=row['produto_id'],
        quantidade=-row['quantidade'],
        origem='FATURAMENTO',
        pedido_id=row['pedido_id'],
        conn=conn,
        bloquear_saldo_negativo=(resultado_cmv["metodo"] == 'LOTE'),
        alertar_saldo_negativo=(resultado_cmv["metodo"] == 'LOTE'),  # warning de estoque só em modo LOTE
    )

# fora do loop de banco, antes do st.success final:
if alertas_custo_ausente:
    produtos_unicos = ", ".join(sorted(set(alertas_custo_ausente)))
    st.warning(f"⚠️ Produto(s) sem custo cadastrado (CMV registrado como zero): {produtos_unicos}. Cadastre o custo em Produtos.")
```

**Distinção importante mantida:**
- Warning de **estoque negativo/lote** → suprimido em modo `SIMPLIFICADO` (é ruído operacional que a Fase 1 não precisa).
- Warning de **custo ausente no cadastro** → **sempre ativo**, em qualquer modo, porque é um problema de dado cadastral, não de fase de implantação. Sem isso, lucro bruto pode ficar artificialmente inflado sem qualquer sinal visível na tela.

## 6. Tela de configuração (sem alteração de fundo, apenas sem tenant_id)

```python
modo_atual = get_config("modo_estoque", conn, default="LOTE")
novo_modo = st.selectbox(
    "Modo de controle de estoque/CMV",
    options=["SIMPLIFICADO", "LOTE"],
    index=0 if modo_atual == "SIMPLIFICADO" else 1,
    help="SIMPLIFICADO: usa custo cadastrado no produto, sem controle de lote (recomendado para Fase 1). LOTE: controle FIFO por lote físico (Fase 2+)."
)
if st.button("Salvar configuração"):
    salvar_config("modo_estoque", novo_modo, conn)
    st.success("Configuração atualizada.")
```

---

## Critério de aceite

1. Com `modo_estoque = 'SIMPLIFICADO'`: faturar pedido de produto com estoque negativo em lote → **nenhum** warning de estoque aparece; `vendas.cmv_metodo = 'SIMPLIFICADO'`; `custo_cmv_real` calculado a partir de `custo_medio` (ou `custo_unidade` se `custo_medio` for zero).
2. Zerar manualmente `custo_medio` E `custo_unidade` de um produto de teste, faturar um pedido com ele → aparece o warning agrupado de "custo ausente", e `custo_cmv_real` é gravado como `0`.
3. Confirmar que `estoque_movimentos` recebe o registro do movimento mesmo em modo `SIMPLIFICADO` (consulta direta no banco).
4. Trocar para `modo_estoque = 'LOTE'` → comportamento antigo (warning de estoque, baixa FIFO) volta sem alteração de código, apenas via configuração.
5. Confirmar que produto com custo cadastrado corretamente, faturado em modo `LOTE`, **não** aciona o warning de custo ausente (já que `custo_ausente` só é avaliado no branch `SIMPLIFICADO`).

---

## Observação para a transição futura (não implementar agora)

Migração para Fase 2 (`modo_estoque = 'LOTE'`) requer inventário físico de abertura antes do switch, para que saldos de lote reflitam a realidade física. Item de roadmap de Fase 2, fora do escopo desta spec.
