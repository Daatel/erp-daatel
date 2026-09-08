# Módulo de Seleção, Metas e Rendimento de Alho
## Especificação Técnica para Implementação — ERP Daatel / Empório do Alho

---

## 1. Contexto

Este documento especifica a implementação do módulo de seleção manual de alho no ERP. O módulo substitui o antigo "Centro de Comando de Produção" (em desuso) e é composto por três abas:

1. **Painel de Produção** — BI mensal com gráfico de barras diário e análise de metas
2. **Mesa de Seleção** — operação do dia: presença, pesagem e descarte
3. **Configurações** — parâmetros administrativos (restrito ao perfil ADMIN)

---

## 2. Alterações no Banco de Dados

### ⚠️ ATENÇÃO ANTIGRAVITY — VERIFICAR CONFLITOS DE NOMENCLATURA
> Antes de executar qualquer migration, verificar se os seguintes nomes já existem no banco de dados atual:
> - Tabela `pessoas` — verificar campos existentes
> - Qualquer tabela com prefixo `selecao_`, `pesagem_`, `meta_`, `presenca_`, `aproveitamento_`
> - Funções ou views com nomes listados abaixo

---

### 2.1. Alteração na tabela existente: `pessoas`

```sql
-- Adicionar campos condicionais para selecionadoras
-- VERIFICAR: se já existem colunas vinculo, nivel, status_ativo na tabela pessoas

ALTER TABLE pessoas
  ADD COLUMN IF NOT EXISTS vinculo VARCHAR(10) DEFAULT NULL,
    -- Valores: 'CLT' | 'Diarista'
    -- Obrigatório apenas quando cargo = 'Selecionadora'

  ADD COLUMN IF NOT EXISTS nivel_classificacao VARCHAR(10) DEFAULT NULL,
    -- Valores: 'A' | 'B' | 'Teste'
    -- Obrigatório apenas quando cargo = 'Selecionadora'

  ADD COLUMN IF NOT EXISTS status_ativa BOOLEAN DEFAULT TRUE;
    -- True = ativa (aparece nas listas operacionais)
    -- False = inativa (arquivada, não aparece)
```

---

### 2.2. Nova tabela: `selecao_metas_nivel`

```sql
-- Parametrização de meta kg/dia por nível de classificação
-- Editável pelo ADMIN na aba Configurações

CREATE TABLE IF NOT EXISTS selecao_metas_nivel (
  nivel          VARCHAR(10)   PRIMARY KEY,  -- 'A' | 'B' | 'Teste'
  meta_kg_dia    DECIMAL(8,2)  NOT NULL,     -- ex: 90.00, 70.00, 50.00
  descricao      VARCHAR(100)  NOT NULL,
  atualizado_em  TIMESTAMP     DEFAULT NOW(),
  atualizado_por INTEGER       REFERENCES pessoas(id)
);

-- Seed inicial
INSERT INTO selecao_metas_nivel (nivel, meta_kg_dia, descricao) VALUES
  ('A',     90.00, 'Alta performance / assídua'),
  ('B',     70.00, 'Rendimento padrão'),
  ('Teste', 50.00, 'Em treinamento / avaliação')
ON CONFLICT (nivel) DO NOTHING;
```

---

### 2.3. Nova tabela: `selecao_parametros`

```sql
-- Parâmetros globais de produção
-- Um registro por mês. Editável pelo ADMIN.

CREATE TABLE IF NOT EXISTS selecao_parametros (
  id                      SERIAL PRIMARY KEY,
  mes_ano                 DATE          NOT NULL UNIQUE,
    -- Sempre o primeiro dia do mês: '2026-07-01'
  meta_diaria_casa_kg     DECIMAL(8,2)  NOT NULL DEFAULT 500.00,
    -- Produção mínima para cobrir custos fixos
  dias_uteis_calculados   INTEGER       NOT NULL DEFAULT 22,
    -- Calculado automaticamente (dias do mês - sábados - domingos)
  dias_uteis_efetivos     INTEGER       NOT NULL DEFAULT 22,
    -- Após aplicar exceções (feriados removidos, sábados adicionados)
  meta_mensal_kg          DECIMAL(10,2) GENERATED ALWAYS AS
                            (meta_diaria_casa_kg * dias_uteis_efetivos) STORED,
  atualizado_em           TIMESTAMP     DEFAULT NOW()
);
```

---

### 2.4. Nova tabela: `selecao_excecoes_calendario`

```sql
-- Exceções ao calendário padrão (feriados, sábados trabalhados)

CREATE TABLE IF NOT EXISTS selecao_excecoes_calendario (
  id          SERIAL PRIMARY KEY,
  data        DATE          NOT NULL UNIQUE,
  tipo        VARCHAR(10)   NOT NULL,
    -- 'REMOVER' = feriado/ponto facultativo (desconta dia útil)
    -- 'ADICIONAR' = sábado/domingo trabalhado (soma dia útil)
  descricao   VARCHAR(100),
  criado_em   TIMESTAMP     DEFAULT NOW(),
  criado_por  INTEGER       REFERENCES pessoas(id)
);
```

---

### 2.5. Nova tabela: `selecao_presenca_diaria`

```sql
-- Registro de presença por selecionadora por dia
-- Criado no Passo 1 da Mesa de Seleção

CREATE TABLE IF NOT EXISTS selecao_presenca_diaria (
  id                  SERIAL PRIMARY KEY,
  data                DATE      NOT NULL,
  selecionadora_id    INTEGER   NOT NULL REFERENCES pessoas(id),
  confirmado_por      INTEGER   REFERENCES pessoas(id),
  confirmado_em       TIMESTAMP DEFAULT NOW(),

  UNIQUE (data, selecionadora_id)
);

CREATE INDEX IF NOT EXISTS idx_presenca_data
  ON selecao_presenca_diaria (data);
```

---

### 2.6. Nova tabela: `selecao_pesagens_diarias`

```sql
-- Lançamento de produção individual por dia

CREATE TABLE IF NOT EXISTS selecao_pesagens_diarias (
  id                    SERIAL PRIMARY KEY,
  data                  DATE          NOT NULL,
  selecionadora_id      INTEGER       NOT NULL REFERENCES pessoas(id),
  peso_kg               DECIMAL(8,2)  NOT NULL CHECK (peso_kg >= 0),
  meta_esperada_kg      DECIMAL(8,2)  NOT NULL,
    -- Snapshot da meta no momento do lançamento (histórico imutável)
  pct_atingimento       DECIMAL(5,2)  GENERATED ALWAYS AS
                          (CASE WHEN meta_esperada_kg > 0
                           THEN (peso_kg / meta_esperada_kg * 100)
                           ELSE 0 END) STORED,
  lancado_por           INTEGER       REFERENCES pessoas(id),
  lancado_em            TIMESTAMP     DEFAULT NOW(),

  UNIQUE (data, selecionadora_id)
);

CREATE INDEX IF NOT EXISTS idx_pesagem_data
  ON selecao_pesagens_diarias (data);

CREATE INDEX IF NOT EXISTS idx_pesagem_selecionadora
  ON selecao_pesagens_diarias (selecionadora_id, data);
```

---

### 2.7. Nova tabela: `selecao_aproveitamento_diario`

```sql
-- Registro de rendimento do lote por dia (Nobre / 2ª Linha / Descarte)

CREATE TABLE IF NOT EXISTS selecao_aproveitamento_diario (
  id                    SERIAL PRIMARY KEY,
  data                  DATE          NOT NULL UNIQUE,
  peso_nobre_kg         DECIMAL(8,2)  NOT NULL DEFAULT 0,
  peso_segunda_linha_kg DECIMAL(8,2)  NOT NULL DEFAULT 0,
  peso_descarte_kg      DECIMAL(8,2)  NOT NULL DEFAULT 0,
  peso_total_kg         DECIMAL(8,2)  GENERATED ALWAYS AS
                          (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) STORED,
  pct_nobre             DECIMAL(5,2)  GENERATED ALWAYS AS
                          (CASE WHEN (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) > 0
                           THEN peso_nobre_kg / (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) * 100
                           ELSE 0 END) STORED,
  pct_segunda_linha     DECIMAL(5,2)  GENERATED ALWAYS AS
                          (CASE WHEN (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) > 0
                           THEN peso_segunda_linha_kg / (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) * 100
                           ELSE 0 END) STORED,
  pct_descarte          DECIMAL(5,2)  GENERATED ALWAYS AS
                          (CASE WHEN (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) > 0
                           THEN peso_descarte_kg / (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) * 100
                           ELSE 0 END) STORED,
  lancado_por           INTEGER       REFERENCES pessoas(id),
  lancado_em            TIMESTAMP     DEFAULT NOW()
);
```

---

### 2.8. Nova tabela: `selecao_historico_nivel`

```sql
-- Histórico de mudanças de nível por selecionadora
-- Permite análise de evolução de performance ao longo do tempo

CREATE TABLE IF NOT EXISTS selecao_historico_nivel (
  id                SERIAL PRIMARY KEY,
  selecionadora_id  INTEGER       NOT NULL REFERENCES pessoas(id),
  nivel_anterior    VARCHAR(10),
  nivel_novo        VARCHAR(10)   NOT NULL,
  data_inicio       DATE          NOT NULL,
  data_fim          DATE,           -- NULL = vigente
  alterado_por      INTEGER       REFERENCES pessoas(id),
  alterado_em       TIMESTAMP     DEFAULT NOW()
);
```

---

## 3. Queries Principais (para o backend Python)

### 3.1. Selecionadoras ativas para a droplist de presença

```sql
SELECT
  p.id,
  p.nome,
  p.vinculo,
  p.nivel_classificacao,
  mn.meta_kg_dia
FROM pessoas p
JOIN selecao_metas_nivel mn ON mn.nivel = p.nivel_classificacao
WHERE p.cargo = 'Selecionadora'
  AND p.status_ativa = TRUE
ORDER BY p.nome;
```

### 3.2. Produção diária do mês para o gráfico de barras

```sql
SELECT
  pd.data,
  SUM(pd.peso_kg)                                      AS producao_total_kg,
  COUNT(pd.selecionadora_id)                           AS n_presentes,
  ROUND(AVG(pd.pct_atingimento), 1)                    AS media_atingimento_pct,
  ROUND(SUM(pd.peso_kg) / NULLIF(COUNT(*), 0), 1)     AS media_por_selecionadora_kg,
  sp.meta_diaria_casa_kg
FROM selecao_pesagens_diarias pd
JOIN selecao_parametros sp ON sp.mes_ano = DATE_TRUNC('month', pd.data)
WHERE DATE_TRUNC('month', pd.data) = :mes_ano
GROUP BY pd.data, sp.meta_diaria_casa_kg
ORDER BY pd.data;
```

### 3.3. Cards de resumo do mês (KPIs)

```sql
WITH dados_mes AS (
  SELECT
    SUM(peso_kg)                    AS realizado_kg,
    COUNT(DISTINCT data)            AS dias_trabalhados,
    COUNT(DISTINCT selecionadora_id) AS total_lancamentos
  FROM selecao_pesagens_diarias
  WHERE DATE_TRUNC('month', data) = :mes_ano
),
dias_acima AS (
  SELECT COUNT(*) AS dias_ok
  FROM (
    SELECT data, SUM(peso_kg) AS total
    FROM selecao_pesagens_diarias
    WHERE DATE_TRUNC('month', data) = :mes_ano
    GROUP BY data
    HAVING SUM(peso_kg) >= (
      SELECT meta_diaria_casa_kg FROM selecao_parametros
      WHERE mes_ano = :mes_ano
    )
  ) sub
),
params AS (
  SELECT meta_diaria_casa_kg, dias_uteis_efetivos, meta_mensal_kg
  FROM selecao_parametros
  WHERE mes_ano = :mes_ano
)
SELECT
  d.realizado_kg,
  p.meta_mensal_kg,
  p.meta_diaria_casa_kg,
  p.dias_uteis_efetivos,
  d.dias_trabalhados,
  da.dias_ok                        AS dias_acima_meta,
  -- Projetado: ritmo atual × dias úteis totais
  ROUND(d.realizado_kg / NULLIF(d.dias_trabalhados, 0)
        * p.dias_uteis_efetivos, 0) AS projetado_kg,
  -- Necessário por dia para fechar o mês
  ROUND(
    (p.meta_mensal_kg - d.realizado_kg) /
    NULLIF(p.dias_uteis_efetivos - d.dias_trabalhados, 0)
  , 0)                              AS necessario_por_dia_kg
FROM dados_mes d, params p, dias_acima da;
```

### 3.4. Salvar presença do dia

```sql
INSERT INTO selecao_presenca_diaria (data, selecionadora_id, confirmado_por)
VALUES (:data, :selecionadora_id, :usuario_id)
ON CONFLICT (data, selecionadora_id) DO NOTHING;
```

### 3.5. Salvar pesagem individual

```sql
INSERT INTO selecao_pesagens_diarias
  (data, selecionadora_id, peso_kg, meta_esperada_kg, lancado_por)
VALUES
  (:data, :selecionadora_id, :peso_kg, :meta_esperada_kg, :usuario_id)
ON CONFLICT (data, selecionadora_id)
DO UPDATE SET
  peso_kg          = EXCLUDED.peso_kg,
  meta_esperada_kg = EXCLUDED.meta_esperada_kg,
  lancado_por      = EXCLUDED.lancado_por,
  lancado_em       = NOW();
```

### 3.6. Salvar aproveitamento do lote

```sql
INSERT INTO selecao_aproveitamento_diario
  (data, peso_nobre_kg, peso_segunda_linha_kg, peso_descarte_kg, lancado_por)
VALUES
  (:data, :peso_nobre_kg, :peso_segunda_linha_kg, :peso_descarte_kg, :usuario_id)
ON CONFLICT (data)
DO UPDATE SET
  peso_nobre_kg         = EXCLUDED.peso_nobre_kg,
  peso_segunda_linha_kg = EXCLUDED.peso_segunda_linha_kg,
  peso_descarte_kg      = EXCLUDED.peso_descarte_kg,
  lancado_por           = EXCLUDED.lancado_por,
  lancado_em            = NOW();
```

---

## 4. Estrutura do Arquivo Python — `pages/Selecao.py`

```
pages/
└── Selecao.py          ← arquivo principal (substituir Producao.py)

components/
└── selecao/
    ├── __init__.py
    ├── painel_bi.py    ← aba 1: gráfico + cards
    ├── mesa.py         ← aba 2: presença + pesagem + descarte
    ├── configuracoes.py← aba 3: metas + calendário
    ├── queries.py      ← todas as queries SQL
    └── pdf_folha.py    ← geração do PDF da folha do dia
```

---

## 5. Checklist de Conflitos — Para o Antigravity Verificar

### Tabela `pessoas`
- [ ] Existe coluna `vinculo`? Se sim, qual tipo e valores?
- [ ] Existe coluna `nivel_classificacao`? Se sim, qual tipo e valores?
- [ ] Existe coluna `status_ativa`? Se sim, conflita com `status_ativo` ou similar?
- [ ] Existe coluna `cargo`? Qual é o valor exato para selecionadoras?

### Nomenclatura de tabelas novas
- [ ] `selecao_metas_nivel` — existe?
- [ ] `selecao_parametros` — existe?
- [ ] `selecao_excecoes_calendario` — existe?
- [ ] `selecao_presenca_diaria` — existe?
- [ ] `selecao_pesagens_diarias` — existe?
- [ ] `selecao_aproveitamento_diario` — existe?
- [ ] `selecao_historico_nivel` — existe?

### Página Python
- [ ] Existe `pages/Producao.py`? Deve ser substituído ou renomeado?
- [ ] Existe `pages/Selecao.py`? Conflito de nome?
- [ ] Existe pasta `components/selecao/`? Conflito?

### Variáveis de sessão (`st.session_state`)
- [ ] `presencas_confirmadas` — em uso em outro módulo?
- [ ] `data_selecao` — em uso em outro módulo?
- [ ] `mes_ano_bi` — em uso em outro módulo?

---

## 6. Observações de Implementação

1. **Colunas calculadas (GENERATED ALWAYS AS STORED):** Requerem PostgreSQL 12+. Se a versão for inferior, implementar como triggers ou calcular no Python.

2. **Snapshot de meta:** O campo `meta_esperada_kg` em `selecao_pesagens_diarias` deve ser preenchido com o valor de `selecao_metas_nivel.meta_kg_dia` no momento do lançamento — nunca buscado dinamicamente no histórico.

3. **Dias úteis:** O cálculo automático de dias úteis deve ser feito em Python com a lib `pandas` ou `numpy` usando `busday_count`, aplicando as exceções de `selecao_excecoes_calendario`.

4. **Geração do PDF:** Usar ReportLab conforme código em `pdf_folha.py`. O PDF é gerado on-demand — não salvo no banco.

5. **Perfil ADMIN:** A aba Configurações deve verificar `st.session_state.perfil == 'ADMIN'` antes de renderizar. Se não for ADMIN, exibir mensagem de acesso restrito.

6. **ON CONFLICT nas pesagens:** Permitir relançamento no mesmo dia (operador corrige valor). O histórico de alterações não é rastreado nesta versão.
