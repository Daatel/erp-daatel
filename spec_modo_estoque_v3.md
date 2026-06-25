# Spec Técnica v3: Modo de Estoque (SIMPLIFICADO/LOTE)

> **Contexto para o agente:** ERP em Python/Streamlit (Gestão Fábrica de Alho), banco SQLite/PostgreSQL, single-tenant. Parte 1 (bugfix `st.rerun()`) já implementada/commitada. Esta v3 substitui a v2: em vez de criar funções novas e alterar o loop de `pages/7_Faturamento.py`, a lógica do modo simplificado é encapsulada **dentro** das funções centrais já existentes (`consumir_estoque_fifo_tx` e `consumir_estoque_fifo`), que já são usadas por Faturamento, PDV Express e Pedidos de Venda/Amostras. Isso evita reescrever a lógica em 3 lugares e elimina o risco de cobertura parcial do switch.

---

## 0. Investigação obrigatória antes de codificar

Antes de qualquer alteração, o agente deve:

1. Abrir `database.py` e listar **todos os call sites** de `consumir_estoque_fifo_tx` e `consumir_estoque_fifo` (grep no projeto inteiro, não só nas páginas já conhecidas). Confirmar quais arquivos/páginas chamam cada uma e como o retorno é desestruturado hoje (provavelmente algo como `custo_total, is_estimado = consumir_estoque_fifo_tx(...)`).
2. Verificar o schema da tabela `estoque_movimentos`: a coluna `lote_origem_id` tem constraint `NOT NULL` e/ou `FOREIGN KEY`? Se sim, anotar — será necessário `ALTER TABLE` para permitir `NULL` antes de gravar movimentos em modo `SIMPLIFICADO`.
3. Verificar se existem telas/relatórios que fazem `JOIN`, `GROUP BY` ou filtro sobre `lote_origem_id` (ex: posição de estoque por lote, relatório de validade) — listar esses pontos para tratamento de `NULL` na Parte 4 desta spec.

Reportar os achados antes de prosseguir para a implementação, mesmo que a investigação confirme que está tudo como esperado.

---

## 1. Schema

```sql
CREATE TABLE IF NOT EXISTS configuracoes_sistema (
    chave   VARCHAR(50) PRIMARY KEY,
    valor   VARCHAR(50) NOT NULL
);
```

Inicialização diferenciada por banco (não usar `ON CONFLICT` genérico — sintaxe diverge entre SQLite e PostgreSQL):

```python
def inicializar_config_modo_estoque(cursor, is_pg: bool):
    if is_pg:
        cursor.execute(
            """INSERT INTO configuracoes_sistema (chave, valor)
               VALUES ('modo_estoque', 'SIMPLIFICADO')
               ON CONFLICT (chave) DO NOTHING"""
        )
    else:
        cursor.execute(
            """INSERT OR IGNORE INTO configuracoes_sistema (chave, valor)
               VALUES ('modo_estoque', 'SIMPLIFICADO')"""
        )
```

Cadastro de produto:
```sql
ALTER TABLE produtos ADD COLUMN IF NOT EXISTS custo_medio NUMERIC(12,2) DEFAULT 0;
```

Rastreabilidade do método (adicionar ao script de migração automática de boot do `database.py`, não como SQL solto):
```python
"ALTER TABLE vendas ADD COLUMN cmv_metodo TEXT DEFAULT 'LOTE'"
```

Se a investigação do item 0.2 confirmar `NOT NULL`/`FK` em `lote_origem_id`, adicionar também ao script de migração a alteração necessária para permitir `NULL` nessa coluna.

---

## 2. Encapsulamento nas funções centrais (`database.py`)

### 2.1 — Helper de leitura de config (com cache por transação)

```python
def _get_modo_estoque(cursor, is_pg: bool) -> str:
    cursor.execute(
        "SELECT valor FROM configuracoes_sistema WHERE chave = %s" if is_pg else
        "SELECT valor FROM configuracoes_sistema WHERE chave = ?",
        ("modo_estoque",)
    )
    row = cursor.fetchone()
    return row[0] if row else "LOTE"
```

### 2.2 — `consumir_estoque_fifo_tx` (versão transacional, usada em Faturamento)

**Assinatura nova:** aceita `modo_estoque` opcional, para permitir que o chamador busque a config **uma vez por transação** (não uma vez por item do loop) e evite N `SELECT`s redundantes quando há múltiplos itens no mesmo pedido/faturamento.

```python
def consumir_estoque_fifo_tx(cursor, produto_id, quantidade, data_mov, origem, doc_ref, modo_estoque=None):
    """
    Consome estoque registrando movimentação.
    modo_estoque: se None, busca em configuracoes_sistema (1 SELECT).
                  Se já fornecido pelo chamador (recomendado em loops), reutiliza sem nova consulta.
    Retorna: (custo_total, is_estimado, cmv_metodo, custo_ausente)
    """
    is_pg = "DATABASE_URL" in st.secrets

    modo = modo_estoque if modo_estoque is not None else _get_modo_estoque(cursor, is_pg)

    if modo == "SIMPLIFICADO":
        cursor.execute(
            "SELECT COALESCE(custo_medio, 0.0), COALESCE(custo_unidade, 0.0) FROM produtos WHERE id = %s" if is_pg else
            "SELECT COALESCE(custo_medio, 0.0), COALESCE(custo_unidade, 0.0) FROM produtos WHERE id = ?",
            (produto_id,)
        )
        row_cost = cursor.fetchone()
        custo_medio = float(row_cost[0]) if row_cost else 0.0
        custo_unidade = float(row_cost[1]) if row_cost else 0.0

        custo_final = custo_medio if custo_medio > 0.0 else custo_unidade
        custo_ausente = custo_final == 0.0
        custo_total = custo_final * float(quantidade)

        cursor.execute(
            """INSERT INTO estoque_movimentos
               (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id)
               VALUES (%s, %s, 'Saída', %s, %s, %s, NULL)""" if is_pg else
            """INSERT INTO estoque_movimentos
               (data, produto_id, tipo_movimento, quantidade, origem, documento_referencia, lote_origem_id)
               VALUES (?, ?, 'Saída', ?, ?, ?, NULL)""",
            (data_mov, produto_id, quantidade, origem, doc_ref)
        )

        return custo_total, False, "SIMPLIFICADO", custo_ausente

    else:
        # Modo LOTE — código FIFO clássico já existente, INALTERADO.
        # ... [manter implementação original integralmente] ...
        # No retorno original, adaptar apenas a tupla final para incluir os dois novos campos:
        return custo_total, is_estimado, "LOTE", False
```

### 2.3 — `consumir_estoque_fifo` (versão não-transacional, usada em PDV Express / Amostras)

**Mesma lógica, mesma assinatura de retorno** — paridade obrigatória com a versão `_tx`. Não é aceitável que PDV Express/Amostras continue em modo LOTE puro enquanto Faturamento respeita o switch; isso recria o problema que esta refatoração existe para evitar (cobertura parcial).

```python
def consumir_estoque_fifo(produto_id, quantidade, data_mov, origem, doc_ref, modo_estoque=None):
    """
    Versão não-transacional (abre própria conexão/cursor).
    Mesma lógica de consumir_estoque_fifo_tx — replicar o branch SIMPLIFICADO/LOTE,
    inclusive registrando em estoque_movimentos com lote_origem_id=NULL quando SIMPLIFICADO.
    Retorna: (custo_total, is_estimado, cmv_metodo, custo_ausente)
    """
    # implementação espelhando 2.2, usando conexão própria (padrão já existente nesta função)
    ...
```

> Se o código atual de `consumir_estoque_fifo` já abre conexão internamente (sem receber `cursor` como parâmetro), manter esse padrão — só replicar o branch de decisão, não unificar as duas funções nesta etapa.

---

## 3. Ajuste nos call sites (Faturamento, PDV Express, Pedidos de Venda)

Para cada call site identificado na investigação do item 0.1:

1. **Atualizar o unpacking do retorno** de `(custo_total, is_estimado)` para `(custo_total, is_estimado, cmv_metodo, custo_ausente)`. Isso vai gerar `ValueError` em qualquer chamada não atualizada — tratar como checklist obrigatório, não como detalhe.
2. **Gravar `cmv_metodo`** na linha de `vendas` (ou tabela equivalente do fluxo, se PDV Express/Amostras gravar em tabela diferente — confirmar na investigação).
3. **Acumular `custo_ausente`** por item processado no fluxo, e exibir UM warning agrupado ao final (fora do loop), não um por item:
   ```python
   if alertas_custo_ausente:
       produtos_unicos = ", ".join(sorted(set(alertas_custo_ausente)))
       st.warning(f"⚠️ Produto(s) sem custo cadastrado (CMV registrado como zero): {produtos_unicos}. Cadastre o custo em Produtos.")
   ```
4. **Buscar `modo_estoque` uma vez**, fora do loop de itens, e passar como parâmetro (`modo_estoque=modo`) em cada chamada à função central — evita N consultas redundantes na mesma transação/fluxo.
5. **Suprimir warning de estoque negativo/lote** apenas quando `cmv_metodo == 'SIMPLIFICADO'` (o warning de custo ausente do item 3 é independente e continua ativo em qualquer modo).

Exemplo de uso no Faturamento:

```python
modo = _get_modo_estoque(cursor, is_pg)  # 1 leitura para toda a transação
alertas_custo_ausente = []

for _, row in pedidos_selecionados.iterrows():
    custo_total, is_estimado, cmv_metodo, custo_ausente = consumir_estoque_fifo_tx(
        cursor, row['produto_id'], row['quantidade'], data_mov, 'FATURAMENTO', row['pedido_id'],
        modo_estoque=modo
    )
    # UPDATE vendas SET status='FATURADO', custo_cmv_real=custo_total, cmv_metodo=cmv_metodo WHERE id=row['pedido_id']

    if custo_ausente:
        alertas_custo_ausente.append(row.get('produto_nome', row['produto_id']))

if alertas_custo_ausente:
    produtos_unicos = ", ".join(sorted(set(alertas_custo_ausente)))
    st.warning(f"⚠️ Produto(s) sem custo cadastrado (CMV registrado como zero): {produtos_unicos}. Cadastre o custo em Produtos.")
```

---

## 4. Tratamento de `lote_origem_id = NULL` em relatórios

Para cada relatório/tela identificado na investigação do item 0.3 que faz `JOIN`/`GROUP BY`/filtro sobre `lote_origem_id`:
- Trocar `JOIN` interno por `LEFT JOIN`, se ainda não for.
- Exibir um rótulo explícito (ex: `"Sem lote (modo simplificado)"`) em vez de omitir a linha ou mostrar célula vazia.

Listar os relatórios afetados como subtarefas explícitas antes de considerar esta parte concluída.

---

## 5. Tela de configuração

```python
modo_atual = _get_modo_estoque(cursor, is_pg)
novo_modo = st.selectbox(
    "Modo de controle de estoque/CMV",
    options=["SIMPLIFICADO", "LOTE"],
    index=0 if modo_atual == "SIMPLIFICADO" else 1,
    help="SIMPLIFICADO: usa custo cadastrado no produto, sem controle de lote (recomendado para Fase 1). LOTE: controle FIFO por lote físico (Fase 2+)."
)
if st.button("Salvar configuração"):
    cursor.execute(
        "UPDATE configuracoes_sistema SET valor = %s WHERE chave = 'modo_estoque'" if is_pg else
        "UPDATE configuracoes_sistema SET valor = ? WHERE chave = 'modo_estoque'",
        (novo_modo,)
    )
    conn.commit()
    st.success("Configuração atualizada.")
```

---

## Critério de aceite

1. **Cobertura completa:** faturar um pedido (Faturamento), registrar uma venda no PDV Express, e lançar uma amostra/degustação — todos os três fluxos respeitam `modo_estoque` sem warning de estoque negativo quando `SIMPLIFICADO`, e todos gravam `cmv_metodo` corretamente.
2. **Fallback de custo:** produto com `custo_medio = 0` mas `custo_unidade > 0` → CMV calculado a partir de `custo_unidade`, sem warning de custo ausente.
3. **Alerta de cadastro:** produto com ambos os custos zerados → warning agrupado de custo ausente aparece, `custo_cmv_real` gravado como `0`, **em qualquer modo** (testar também em `LOTE`, onde `custo_ausente` deve ser sempre `False` por definição — produto sem custo em modo LOTE é tratado pela lógica de estimativa já existente, não por este novo alerta).
4. **`estoque_movimentos`:** confirmar registro do movimento com `lote_origem_id = NULL` em modo `SIMPLIFICADO`, sem erro de constraint.
5. **Relatórios:** abrir cada relatório listado na investigação do item 0.3 e confirmar que movimentos com `lote_origem_id = NULL` aparecem com rótulo apropriado, não omitidos nem quebrando a tela.
6. **Regressão:** com `modo_estoque = 'LOTE'`, todo o comportamento atual (FIFO, `is_estimado`, warnings de estoque) permanece idêntico ao pré-existente nos três fluxos.
7. **Sem ValueError:** confirmar que nenhum call site de `consumir_estoque_fifo_tx`/`consumir_estoque_fifo` ficou com unpacking desatualizado (2 valores em vez de 4).

---

## Observação para a transição futura (não implementar agora)

Migração para `LOTE` em produção requer inventário físico de abertura. Item de roadmap de Fase 2, fora do escopo desta spec.
