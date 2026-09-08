# Módulo de Seleção — Especificação Técnica Consolidada
## ERP Daatel / Empório do Alho
### Versão 2.0 — inclui Mesa de Seleção, OCR e Ranking

---

## 1. Visão Geral

Este documento consolida toda a especificação técnica do módulo de seleção
manual de alho. Substitui versões anteriores.

### Estrutura de abas

```
pages/Selecao.py
├── 📊 Painel de produção   → painel_bi.py
├── 🧄 Mesa de seleção      → mesa.py  (+  ocr_folha.py)
├── 🏆 Ranking              → ranking.py
└── ⚙️  Configurações        → configuracoes.py  (restrito ADMIN)
```

---

## 2. Arquivos do Módulo

```
pages/
└── Selecao.py                  ← página principal (substituir Producao.py)

components/selecao/
├── __init__.py
├── painel_bi.py                ← aba 1: KPIs + gráfico diário
├── mesa.py                     ← aba 2: presença + pesagem + descarte
├── ocr_folha.py                ← componente OCR (integrado à mesa)
├── ranking.py                  ← aba 3: ranking + histórico individual
├── configuracoes.py            ← aba 4: metas + calendário (ADMIN)
├── queries.py                  ← todas as queries SQL centralizadas
└── pdf_folha.py                ← gerador PDF da folha do dia
```

---

## 3. Banco de Dados

### ⚠️ CHECKLIST ANTIGRAVITY — verificar antes de executar a migration

#### Tabela `pessoas` — verificar se já existem:
- [ ] Coluna `vinculo` — tipo e valores atuais?
- [ ] Coluna `nivel_classificacao` — tipo e valores atuais?
- [ ] Coluna `status_ativa` — conflita com `status_ativo` ou similar?
- [ ] Coluna `cargo` — qual o valor exato para selecionadoras?

#### Tabelas novas — verificar se já existem:
- [ ] `selecao_metas_nivel`
- [ ] `selecao_parametros`
- [ ] `selecao_excecoes_calendario`
- [ ] `selecao_presenca_diaria`
- [ ] `selecao_pesagens_diarias`
- [ ] `selecao_aproveitamento_diario`
- [ ] `selecao_historico_nivel`

#### Arquivos Python — verificar conflitos:
- [ ] `pages/Producao.py` — substituir ou renomear?
- [ ] `pages/Selecao.py` — já existe?
- [ ] `components/selecao/` — pasta já existe?

#### Variáveis de session_state — verificar se já estão em uso:
- [ ] `selecao_mes_ano`
- [ ] `selecao_presencas_confirmadas`
- [ ] `selecao_passo`
- [ ] `ocr_pesos_confirmados`
- [ ] `ocr_importacao_ok`
- [ ] `ranking_selecionada`

#### Dependências Python — verificar requirements.txt:
- [ ] `google-generativeai` — instalado?
- [ ] `pillow` — instalado?
- [ ] `altair` — instalado?
- [ ] `GEMINI_API_KEY` — configurada em secrets?

---

### 3.1. Alteração na tabela `pessoas`

```sql
ALTER TABLE pessoas
  ADD COLUMN IF NOT EXISTS vinculo VARCHAR(10) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS nivel_classificacao VARCHAR(10) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS status_ativa BOOLEAN DEFAULT TRUE;
```

---

### 3.2. Novas tabelas

```sql
-- Metas por nível
CREATE TABLE IF NOT EXISTS selecao_metas_nivel (
  nivel          VARCHAR(10)   PRIMARY KEY,  -- 'A' | 'B' | 'Teste'
  meta_kg_dia    DECIMAL(8,2)  NOT NULL,
  descricao      VARCHAR(100)  NOT NULL,
  atualizado_em  TIMESTAMP     DEFAULT NOW(),
  atualizado_por INTEGER       REFERENCES pessoas(id)
);

INSERT INTO selecao_metas_nivel (nivel, meta_kg_dia, descricao) VALUES
  ('A',     90.00, 'Alta performance / assídua'),
  ('B',     70.00, 'Rendimento padrão'),
  ('Teste', 50.00, 'Em treinamento / avaliação')
ON CONFLICT (nivel) DO NOTHING;

-- Parâmetros mensais
CREATE TABLE IF NOT EXISTS selecao_parametros (
  id                    SERIAL PRIMARY KEY,
  mes_ano               DATE          NOT NULL UNIQUE,
  meta_diaria_casa_kg   DECIMAL(8,2)  NOT NULL DEFAULT 500.00,
  dias_uteis_calculados INTEGER       NOT NULL DEFAULT 22,
  dias_uteis_efetivos   INTEGER       NOT NULL DEFAULT 22,
  atualizado_em         TIMESTAMP     DEFAULT NOW()
);

-- Exceções de calendário
CREATE TABLE IF NOT EXISTS selecao_excecoes_calendario (
  id          SERIAL PRIMARY KEY,
  data        DATE          NOT NULL UNIQUE,
  tipo        VARCHAR(10)   NOT NULL CHECK (tipo IN ('REMOVER', 'ADICIONAR')),
  descricao   VARCHAR(100),
  criado_em   TIMESTAMP     DEFAULT NOW(),
  criado_por  INTEGER       REFERENCES pessoas(id)
);

-- Presença diária
CREATE TABLE IF NOT EXISTS selecao_presenca_diaria (
  id                SERIAL PRIMARY KEY,
  data              DATE      NOT NULL,
  selecionadora_id  INTEGER   NOT NULL REFERENCES pessoas(id),
  confirmado_por    INTEGER   REFERENCES pessoas(id),
  confirmado_em     TIMESTAMP DEFAULT NOW(),
  UNIQUE (data, selecionadora_id)
);
CREATE INDEX IF NOT EXISTS idx_presenca_data ON selecao_presenca_diaria (data);

-- Pesagens diárias
CREATE TABLE IF NOT EXISTS selecao_pesagens_diarias (
  id                SERIAL PRIMARY KEY,
  data              DATE          NOT NULL,
  selecionadora_id  INTEGER       NOT NULL REFERENCES pessoas(id),
  peso_kg           DECIMAL(8,2)  NOT NULL CHECK (peso_kg >= 0),
  meta_esperada_kg  DECIMAL(8,2)  NOT NULL,
  lancado_por       INTEGER       REFERENCES pessoas(id),
  lancado_em        TIMESTAMP     DEFAULT NOW(),
  UNIQUE (data, selecionadora_id)
);
CREATE INDEX IF NOT EXISTS idx_pesagem_data ON selecao_pesagens_diarias (data);
CREATE INDEX IF NOT EXISTS idx_pesagem_selecionadora ON selecao_pesagens_diarias (selecionadora_id, data);

-- Aproveitamento diário do lote
CREATE TABLE IF NOT EXISTS selecao_aproveitamento_diario (
  id                    SERIAL PRIMARY KEY,
  data                  DATE          NOT NULL UNIQUE,
  peso_nobre_kg         DECIMAL(8,2)  NOT NULL DEFAULT 0,
  peso_segunda_linha_kg DECIMAL(8,2)  NOT NULL DEFAULT 0,
  peso_descarte_kg      DECIMAL(8,2)  NOT NULL DEFAULT 0,
  lancado_por           INTEGER       REFERENCES pessoas(id),
  lancado_em            TIMESTAMP     DEFAULT NOW()
);

-- Histórico de nível por selecionadora
CREATE TABLE IF NOT EXISTS selecao_historico_nivel (
  id                SERIAL PRIMARY KEY,
  selecionadora_id  INTEGER       NOT NULL REFERENCES pessoas(id),
  nivel_anterior    VARCHAR(10),
  nivel_novo        VARCHAR(10)   NOT NULL,
  data_inicio       DATE          NOT NULL,
  data_fim          DATE,
  alterado_por      INTEGER       REFERENCES pessoas(id),
  alterado_em       TIMESTAMP     DEFAULT NOW()
);
```

---

## 4. Fluxos por Aba

### 4.1. Painel de Produção (BI)

```
Seletor de mês (◀ Julho 2026 ▶)
    ↓
5 cards de KPI:
  Realizado | Projetado | Meta total | Dias acima meta | Necessário/dia
    ↓
Gráfico de barras diário
  Barras: verde (acima meta) / vermelho (abaixo)
  Linha azul:    meta mínima da casa
  Linha tracejada âmbar: necessário/dia para fechar o mês (dias futuros)
    ↓
2 cards inferiores:
  Média de presentes/dia | Média kg/selecionadora
```

**Fórmula do Necessário/dia:**
```
Necessário/dia = (Meta mensal - Realizado até hoje) ÷ Dias úteis restantes
```

---

### 4.2. Mesa de Seleção

```
Passo 1 — Presença
  Multiselect de selecionadoras ativas
  Cards: presentes | capacidade do dia | meta da casa
  Botão: Confirmar presença → salva em selecao_presenca_diaria
    ↓
Passo 2 — Pesagem individual
  [Expander] 📷 Importar folha fotografada  ← OCR (ver 4.2.1)
  Tabela: nome | meta | input kg | barra de progresso %
    ↓
Passo 3 — Descarte × 2ª linha
  Inputs: Alho nobre | 2ª linha | Descarte
  Cálculo automático de percentuais
    ↓
Botão: Salvar lançamentos do dia
  → selecao_pesagens_diarias (upsert por data+selecionadora)
  → selecao_aproveitamento_diario (upsert por data)
```

#### 4.2.1. Importação via Foto (OCR)

```
Upload / câmera
    ↓
Gemini Vision API (gemini-1.5-flash)
    ↓
JSON: { pesagens: [{nome, total_kg}], nobre_kg, segunda_linha_kg, descarte_kg,
        confianca: alta|media|baixa, avisos: [] }
    ↓
Tabela de confirmação editável
  Match fuzzy de nomes (normaliza acentos, aceita nome parcial)
  Campos null → em branco com alerta ⚠️
  Campos suspeitos (valor > 1.5x meta) → alerta
    ↓
Confirmar importação
  → Preenche campos do Passo 2 e 3 automaticamente
  → Operadora revisa e clica Salvar (mesmo fluxo do manual)
```

**Custo:** < R$ 0,01 por foto. Irrelevante.

**Fallback:** se API falhar, mensagem de erro + lançamento manual continua disponível.

---

### 4.3. Ranking de Selecionadoras

```
Filtros: Período | Vínculo (CLT/Diarista/Todos) | Ordenar por
    ↓
4 cards de resumo do grupo:
  Total | Atingimento médio | Maior produção | Assiduidade média
    ↓
Tabela de ranking (ordenável):
  # | Nome | Nível | Dias presentes | % Assiduidade | Produção total
    | Média/dia | % Atingimento | Tendência ↑→↓ | [Ver histórico]
    ↓
Clicar "Ver histórico" → abre abaixo:
  KPIs individuais (5 cards)
  Gráfico de barras individual com linha de meta
  Tabela detalhe dia a dia (expansível)
```

**Cálculo da Tendência:**
```
Compara média dos últimos 15 dias vs 15 dias anteriores
↑ subindo  = recente > anterior × 1.05
→ estável  = variação < 5%
↓ caindo   = recente < anterior × 0.95
— neutro   = dados insuficientes
```

**Cores de % Atingimento:**
- ≥ 100% → verde
- 80–99% → âmbar
- < 80%  → vermelho

**Cores de % Assiduidade:**
- ≥ 90% → verde
- 70–89% → âmbar
- < 70%  → vermelho

---

### 4.4. Configurações (ADMIN)

```
Guard: perfil != ADMIN → mensagem de acesso restrito
    ↓
Metas por nível (A / B / Teste) — editável
    ↓
Meta mínima da casa (kg/dia) — editável por mês
    ↓
Calendário do mês:
  Dias úteis: calculado automaticamente (sem sáb/dom)
  Exceções: adicionar/remover feriados e sábados trabalhados
  Info box: dias úteis efetivos + meta mensal resultante
    ↓
Botão: Salvar configurações
  → selecao_metas_nivel (upsert)
  → selecao_parametros (upsert)
  → selecao_excecoes_calendario (insert/delete)
```

---

## 5. Patch do mesa.py para integrar OCR

Localizar no `mesa.py` o trecho abaixo do `st.divider()` antes do Passo 2
e adicionar:

```python
# 1. Import no topo
from .ocr_folha import render_importar_folha

# 2. Antes da tabela de pesagem
render_importar_folha(presentes)
ocr_pesos = st.session_state.pop("ocr_pesos_confirmados", {})

# 3. No number_input de cada selecionadora
default_peso = float(ocr_pesos.get(p["id"], {}).get("peso", 0.0))
peso = st.number_input("kg", min_value=0.0, value=default_peso, ...)

# 4. Nos inputs de descarte
peso_nobre    = st.number_input(..., value=float(st.session_state.pop("ocr_nobre_kg", 0.0)))
peso_segunda  = st.number_input(..., value=float(st.session_state.pop("ocr_segunda_linha_kg", 0.0)))
peso_descarte = st.number_input(..., value=float(st.session_state.pop("ocr_descarte_kg", 0.0)))
```

---

## 6. Patch do Selecao.py para adicionar a aba Ranking

```python
# Substituir:
aba_bi, aba_mesa, aba_config = st.tabs([...])

# Por:
aba_bi, aba_mesa, aba_ranking, aba_config = st.tabs([
    "📊 Painel de produção",
    "🧄 Mesa de seleção",
    "🏆 Ranking",
    "⚙️ Configurações",
])

# Adicionar import:
from components.selecao.ranking import render_ranking

# Adicionar bloco:
with aba_ranking:
    render_ranking()
```

---

## 7. Observações de Implementação

1. **Colunas calculadas:** Requerem PostgreSQL 12+. Se versão inferior,
   calcular no Python ou usar triggers.

2. **Snapshot de meta:** `meta_esperada_kg` em `selecao_pesagens_diarias`
   deve ser preenchido no momento do lançamento — nunca buscado dinamicamente.

3. **ON CONFLICT nas pesagens:** Permite relançamento no mesmo dia (correção).
   Histórico de alterações não é rastreado nesta versão.

4. **Gemini Vision:** Usar `gemini-1.5-flash` (rápido e barato).
   Alternativa mais precisa para caligrafia ruim: `gemini-1.5-pro`.
   Campos ilegíveis retornam `null` — nunca inventam valores.

5. **Guard de ADMIN:** Verificar `st.session_state.get("perfil") == "ADMIN"`
   antes de renderizar a aba Configurações.

6. **st.camera_input:** Requer HTTPS em produção. Em desenvolvimento local
   funciona via localhost.

7. **Tendência no ranking:** Calculada na query SQL para evitar lógica
   duplicada no Python. Threshold de 5% evita falsos alarmes por variação
   natural do dia a dia.
