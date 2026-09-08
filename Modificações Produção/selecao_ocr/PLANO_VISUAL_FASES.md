# Plano de Reestruturação Visual — ERP Daatel / Empório do Alho
## Documento de execução para o Antigravity
### Versão 1.0 — Abordagem em 4 fases com rollback seguro

---

## Contexto

O sistema atual apresenta visual pesado devido a três causas identificadas:

1. `config.toml` com `textColor = "#292d77"` (azul) e
   `secondaryBackgroundColor = "#0f172a"` (quase preto)
2. Inputs com 48px de altura padrão do Streamlit ocupando largura total
3. CSS customizado espalhado em 15 arquivos de página sem padrão

A solução é centralizar todo o CSS em um único arquivo `components/theme.py`
e aplicar progressivamente, página por página, com validação a cada etapa.

**Regra de ouro deste plano:**
> Nunca avançar para a próxima fase sem validação explícita da fase anterior.

---

## Arquivos envolvidos

| Arquivo | Ação | Risco |
|---|---|---|
| `.streamlit/config.toml` | Substituir (com backup) | Baixo |
| `components/theme.py` | Criar (arquivo novo) | Zero |
| `pages/99_Tema_Preview.py` | Criar (arquivo novo) | Zero |
| `pages/4_Producao.py` | Adicionar 2 linhas | Baixíssimo |
| Demais páginas (14 arquivos) | Adicionar 2 linhas + remover CSS inline | Médio |

---

## Fase 1 — Criar o tema e validar isoladamente

**Objetivo:** ter o arquivo de tema pronto e visível numa página de teste
sem tocar em nada do sistema em produção.

**Pré-requisito:** nenhum.

### 1.1. Fazer backup do config.toml atual

```bash
cp .streamlit/config.toml .streamlit/config.toml.bak
```

### 1.2. Substituir o config.toml

Substituir o conteúdo de `.streamlit/config.toml` por:

```toml
[theme]
primaryColor = "#01743d"
backgroundColor = "#f9f8f4"
secondaryBackgroundColor = "#ffffff"
textColor = "#1a1a18"
font = "sans serif"
```

### 1.3. Criar components/theme.py

Criar o arquivo `components/theme.py` com o conteúdo fornecido em anexo
(arquivo `theme.py` do pacote `selecao_completo_v3.zip`).

Não modificar nenhum arquivo existente.

### 1.4. Criar a página de preview

Criar `pages/99_Tema_Preview.py` com o conteúdo abaixo.
Essa página não aparece no menu de produção (prefixo 99 a mantém no final)
e pode ser deletada a qualquer momento sem impacto.

```python
# pages/99_Tema_Preview.py
# Página de validação visual do tema — NÃO é funcional, apenas demonstrativa
# Deletar após validação completa de todas as fases

import streamlit as st
from components.theme import (
    apply_theme, Cores,
    badge_nivel, badge_vinculo, badge_status, badge_tendencia,
    metric_card, section_title, divider_line,
)

st.set_page_config(page_title="Preview do Tema", layout="wide")
apply_theme()

st.title("Preview do tema — ERP Daatel")
st.caption("Esta página é apenas para validação visual. Não tem função operacional.")

st.divider()

# ── Inputs ────────────────────────────────────────────────────────────────
st.markdown(section_title("Inputs e controles"), unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.text_input("Campo de texto", placeholder="Digite algo...")
with c2:
    st.number_input("Número", min_value=0.0, value=90.0, step=1.0)
with c3:
    st.selectbox("Selectbox", ["Opção A", "Opção B", "Opção C"])
with c4:
    st.date_input("Data")

st.multiselect(
    "Multiselect",
    ["Maria Souza", "Ana Lima", "Carla Dias", "Fernanda Costa", "Julia Mendes"],
    default=["Maria Souza", "Ana Lima"],
)

st.divider()

# ── Botões ────────────────────────────────────────────────────────────────
st.markdown(section_title("Botões"), unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.button("Botão padrão")
with c2:
    st.button("Botão primário", type="primary")
with c3:
    st.button("↩ Voltar")
with c4:
    st.button("💾 Salvar", type="primary")

st.divider()

# ── Métricas ──────────────────────────────────────────────────────────────
st.markdown(section_title("Métricas (st.metric)"), unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Realizado no mês",    "11.840 kg",  help="Até 25 dias trabalhados")
c2.metric("Projetado até fim",   "14.208 kg",  delta="-1.792 kg vs meta", delta_color="inverse")
c3.metric("Meta total do mês",   "16.000 kg")
c4.metric("Dias acima da meta",  "14 de 18")
c5.metric("Necessário/dia",      "587 kg/dia", delta="4 dias restantes", delta_color="off")

st.divider()

# ── Badges ────────────────────────────────────────────────────────────────
st.markdown(section_title("Badges"), unsafe_allow_html=True)

badges_html = " &nbsp; ".join([
    badge_nivel("A"),
    badge_nivel("B"),
    badge_nivel("Teste"),
    badge_vinculo("CLT"),
    badge_vinculo("Diarista"),
    badge_status(105),
    badge_status(88),
    badge_status(62),
    badge_tendencia("subindo"),
    badge_tendencia("estavel"),
    badge_tendencia("caindo"),
])
st.markdown(badges_html, unsafe_allow_html=True)

st.divider()

# ── Cards de KPI em HTML ──────────────────────────────────────────────────
st.markdown(section_title("Cards de KPI (HTML)"), unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        metric_card("Presentes hoje", "8", "selecionadoras"),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        metric_card("Capacidade do dia", "640 kg"),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        metric_card("Meta da casa", "500 kg", cor_value=Cores.VERDE),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        metric_card("Necessário/dia", "587 kg", "4 dias restantes", Cores.ERRO),
        unsafe_allow_html=True,
    )

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────
st.markdown(section_title("Tabs"), unsafe_allow_html=True)

aba1, aba2, aba3, aba4 = st.tabs([
    "📊 Painel de produção",
    "🧄 Mesa de seleção",
    "🏆 Ranking",
    "⚙️ Configurações",
])

with aba1:
    st.caption("Conteúdo da aba Painel de produção.")
with aba2:
    st.caption("Conteúdo da aba Mesa de seleção.")
with aba3:
    st.caption("Conteúdo da aba Ranking.")
with aba4:
    st.caption("Conteúdo da aba Configurações.")

st.divider()

# ── Expander ──────────────────────────────────────────────────────────────
st.markdown(section_title("Expander"), unsafe_allow_html=True)

with st.expander("📷 Importar folha fotografada"):
    st.caption("Conteúdo do expander. Compacto e com borda fina.")
    st.text_input("Campo dentro do expander", placeholder="Teste...")

st.divider()

# ── Alertas ───────────────────────────────────────────────────────────────
st.markdown(section_title("Alertas"), unsafe_allow_html=True)

st.success("Lançamentos do dia salvos com sucesso.")
st.warning("Campo ilegível identificado — revisar pesagem de Maria Souza.")
st.error("Erro na API Gemini. Use o lançamento manual como alternativa.")
st.info("Dias úteis calculados automaticamente: 22 dias — meta mensal: 11.000 kg.")

st.divider()

# ── Tabela ────────────────────────────────────────────────────────────────
st.markdown(section_title("Tabela (st.dataframe)"), unsafe_allow_html=True)

import pandas as pd
df = pd.DataFrame({
    "Nome":           ["Maria Souza", "Ana Lima", "Carla Dias", "Fernanda Costa"],
    "Nível":          ["A", "A", "B", "B"],
    "Meta (kg)":      [90, 90, 70, 70],
    "Produção (kg)":  [95, 88, 62, 71],
    "Atingimento (%)": [105.6, 97.8, 88.6, 101.4],
})
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.caption("Fim do preview. Deletar esta página após validação completa.")
```

### 1.5. Critério de aprovação da Fase 1

Abrir `pages/99_Tema_Preview.py` no browser e verificar:

- [ ] Texto em grafite escuro (não azul)
- [ ] Fundo off-white suave
- [ ] Inputs com altura ~36px (compactos)
- [ ] Botão primário em verde escuro
- [ ] Métricas com borda fina e padding reduzido
- [ ] Badges coloridos por nível, vínculo e status
- [ ] Tabs com fonte correta
- [ ] Expander com borda fina
- [ ] Alertas compactos

**Se todos os itens estiverem OK → avançar para Fase 2.**
**Se houver problema → corrigir theme.py e repetir. Não avançar.**

---

## Fase 2 — Aplicar em página de baixo risco

**Objetivo:** validar o tema numa página real do sistema.

**Pré-requisito:** Fase 1 aprovada.

**Página escolhida:** `pages/4_Producao.py`

Motivo: esta página está em desuso e será substituída pelo módulo
`Selecao.py`. É o candidato de menor risco do sistema.

### 2.1. Editar pages/4_Producao.py

Adicionar no topo do arquivo, logo após os imports existentes:

```python
from components.theme import apply_theme
```

Adicionar logo após o `st.set_page_config(...)`:

```python
apply_theme()
```

Localizar e remover qualquer bloco do tipo:

```python
st.markdown("""<style> ... </style>""", unsafe_allow_html=True)
```

### 2.2. Critério de aprovação da Fase 2

- [ ] Página de Produção visualmente coerente com o preview
- [ ] Nenhuma outra página do sistema foi afetada
- [ ] Funcionalidade da página mantida (nada quebrou)

**Se OK → avançar para Fase 3.**
**Se houver problema → rollback da página (git checkout ou remoção manual
das 2 linhas adicionadas) e corrigir theme.py.**

---

## Fase 3 — Migrar as páginas existentes

**Objetivo:** aplicar o tema em todas as 14 páginas restantes.

**Pré-requisito:** Fase 2 aprovada.

**Ritmo:** uma página por sessão de trabalho. Nunca mais de uma por vez.

### Ordem sugerida (do menor para o maior risco percebido)

| Ordem | Página | Observação |
|---|---|---|
| 1 | `pages/1_Cadastros.py` | Formulários simples |
| 2 | `pages/3_Pessoas.py` | Formulários simples |
| 3 | `pages/5_Estoque.py` | Tabelas e inputs |
| 4 | `pages/2_Compras.py` | Tabelas e inputs |
| 5 | `pages/8_Logistica.py` | Tabelas e inputs |
| 6 | `pages/6_Pedidos_de_Venda.py` | Fluxo crítico |
| 7 | `pages/7_Faturamento.py` | Fluxo crítico |
| 8 | `pages/9_Financeiro.py` | Fluxo crítico |
| 9 | `pages/14_Tabelas_Preco.py` | Configuração |
| 10 | `pages/11_Ativos_Comodatos.py` | Configuração |
| 11 | `pages/12_Rentabilidade_Cliente.py` | BI |
| 12 | `pages/10_DRE.py` | BI — mais complexo |
| 13 | `pages/13_PDV_Express.py` | PDV — mais crítico |
| 14 | `pages/0_Dashboard.py` | Home — último |

### Procedimento para cada página

**A. Adicionar import e chamada:**

```python
# Adicionar após imports existentes
from components.theme import apply_theme

# Adicionar após st.set_page_config()
apply_theme()
```

**B. Remover CSS inline antigo:**

Localizar e remover blocos do tipo:
```python
st.markdown("""<style> ... </style>""", unsafe_allow_html=True)
```

Manter `st.markdown` que injeta HTML de conteúdo (badges, cards, texto).
Remover apenas os que contêm `<style>`.

**C. Verificar após cada página:**
- [ ] Página abre sem erro
- [ ] Visual coerente com o preview
- [ ] Funcionalidade preservada
- [ ] Nenhuma outra página afetada

**Se qualquer página apresentar problema → parar e corrigir antes de
continuar para a próxima.**

---

## Fase 4 — Novas páginas nascem com o tema

**Objetivo:** garantir que todo código novo já use o padrão.

**Pré-requisito:** Fases 1, 2 e 3 concluídas.

### 4.1. Regra para novas páginas

Todo arquivo novo em `pages/` deve ter obrigatoriamente:

```python
from components.theme import apply_theme

st.set_page_config(page_title="...", layout="wide")
apply_theme()
```

### 4.2. Regra para novos componentes

Novos componentes em `components/` que precisem de HTML devem usar
os helpers do `theme.py`:

```python
from components.theme import (
    badge_nivel, badge_vinculo, badge_status,
    badge_tendencia, metric_card, section_title,
    divider_line, Cores,
)
```

Nunca escrever CSS inline em componentes novos.

### 4.3. Deletar a página de preview

Após validação completa de todas as páginas:

```bash
rm pages/99_Tema_Preview.py
```

### 4.4. Arquivos do módulo Selecao

Os arquivos do pacote `selecao_completo_v3.zip` já foram escritos
com `apply_theme()` incorporado. Nenhuma ação adicional necessária.

---

## Rollback de emergência

Se em qualquer fase o sistema apresentar problema grave:

**Rollback do config.toml:**
```bash
cp .streamlit/config.toml.bak .streamlit/config.toml
```

**Rollback de uma página específica:**
Remover as duas linhas adicionadas:
```python
from components.theme import apply_theme  # ← remover
apply_theme()                              # ← remover
```
E restaurar o bloco `<style>` que foi removido (via git ou backup).

**O theme.py e o 99_Tema_Preview.py são arquivos novos —
deletá-los não afeta nada do sistema existente.**

---

## Resumo executivo

| Fase | O que faz | Toca em produção? | Reversível? |
|---|---|---|---|
| 1 | Cria tema + página de preview | Não | Sim (deletar arquivos) |
| 2 | Aplica em 1 página em desuso | Minimamente | Sim (2 linhas) |
| 3 | Migra 14 páginas, 1 por vez | Sim, gradual | Sim (por página) |
| 4 | Padrão para código novo | Não (preventivo) | N/A |

**Início seguro: executar apenas Fase 1 e aguardar validação.**
