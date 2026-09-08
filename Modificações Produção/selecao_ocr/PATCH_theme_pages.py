# PATCH — Integração do tema nas páginas existentes
# =============================================================================
# Aplicar em TODAS as páginas listadas abaixo.
# Instrução para o Antigravity: buscar e substituir em cada arquivo.
# =============================================================================

# PÁGINAS A ATUALIZAR:
# pages/0_Dashboard.py
# pages/10_DRE.py
# pages/11_Ativos_Comodatos.py
# pages/12_Rentabilidade_Cliente.py
# pages/13_PDV_Express.py
# pages/14_Tabelas_Preco.py
# pages/1_Cadastros.py
# pages/2_Compras.py
# pages/3_Pessoas.py
# pages/4_Producao.py  ← será substituído por Selecao.py
# pages/5_Estoque.py
# pages/6_Pedidos_de_Venda.py
# pages/7_Faturamento.py
# pages/8_Logistica.py
# pages/9_Financeiro.py

# -----------------------------------------------------------------------------
# PASSO 1 — Adicionar import no topo de CADA página
# -----------------------------------------------------------------------------
# Logo após os imports existentes, adicionar:

from components.theme import apply_theme

# -----------------------------------------------------------------------------
# PASSO 2 — Chamar apply_theme() logo após st.set_page_config()
# -----------------------------------------------------------------------------
# Exemplo de como ficará o topo de cada página:

# ANTES:
# st.set_page_config(page_title="...", layout="wide")
# st.markdown("""<style> ... CSS antigo ... </style>""", unsafe_allow_html=True)

# DEPOIS:
# st.set_page_config(page_title="...", layout="wide")
# from components.theme import apply_theme
# apply_theme()
# (remover o st.markdown de CSS que existia antes)

# -----------------------------------------------------------------------------
# PASSO 3 — Remover CSS inline antigo
# -----------------------------------------------------------------------------
# Em cada arquivo, remover blocos do tipo:
#
#   st.markdown("""
#   <style>
#       ...qualquer CSS...
#   </style>
#   """, unsafe_allow_html=True)
#
# Esses blocos agora são cobertos pelo theme.py centralizado.
# ATENÇÃO: manter st.markdown que injeta HTML de conteúdo (badges, cards),
# remover APENAS os que injetam <style>.

# -----------------------------------------------------------------------------
# PASSO 4 — Copiar config.toml para o lugar certo
# -----------------------------------------------------------------------------
# O arquivo config.toml fornecido deve substituir .streamlit/config.toml
# Fazer backup do original antes:
#   cp .streamlit/config.toml .streamlit/config.toml.bak

# -----------------------------------------------------------------------------
# VERIFICAÇÃO após aplicar
# -----------------------------------------------------------------------------
# 1. Rodar o ERP localmente
# 2. Abrir cada página e verificar:
#    - Inputs com altura ~36px (não mais 48px)
#    - Texto em grafite escuro (não mais azul)
#    - Fundo off-white suave
#    - Sidebar escura (grafite)
#    - Métricas com borda fina e padding compacto
# 3. Se alguma página parecer quebrada, verificar se havia CSS conflitante
#    não removido no Passo 3

# -----------------------------------------------------------------------------
# NOVAS PÁGINAS (incluindo Selecao.py)
# -----------------------------------------------------------------------------
# Todas as novas páginas já têm apply_theme() no topo do arquivo.
# Não é necessário nenhuma ação adicional.
