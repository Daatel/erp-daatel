# Projetos Futuros - Melhorias Visuais e de Tipografia

## 🎨 Identidade Visual e Tipologia Moderna
- **Objetivo:** Substituir a tipografia padrão do navegador por fontes modernas e elegantes (como Google Fonts Inter, Roboto ou Outfit) no ERP.
- **Cabeçalhos:** Aplicar a nova tipologia padronizada a todos os títulos de módulos, mantendo a consistência visual (tamanho de fonte reduzido para `2.2rem`, sem emojis e alinhado ao topo com a logo lateral).

---

## 🏷️ Mapeamento de Ícones (Remoção de Emojis do Financeiro)
Abaixo está o mapeamento dos locais e respectivos emojis que foram removidos da página `pages/9_Financeiro.py`, servindo como guia para a futura implementação de uma biblioteca de ícones padronizada (ex: FontAwesome, Lucide ou Material Design Icons):

* **Configuração da Página:**
  - Título original do módulo: `💸 Tesouraria e Inteligência Financeira` (alterado para `Financeiro e Tesouraria`)
  - Ícone original da aba do navegador (`page_icon`): `💸`

* **Abas do Menu Principal (`st.tabs`):**
  - Painel Executivo: `📊 Painel Executivo`
  - Contas a Pagar: `🔻 Contas a Pagar (Saída)`
  - Contas a Receber: `🟢 Contas a Receber (Entrada)`
  - Caixas e Bancos: `🏦 Caixas e Bancos`
  - Auditoria Logística: `🚚 Auditoria Logística`

* **Métricas Principais (KPIs do Dashboard):**
  - KPI de Entrada: `💰 Entra hoje`
  - KPI de Saída: `💸 Sai hoje`
  - KPI de Resultado: `💎 Resultado do dia`

* **Subtítulos e Expanders:**
  - Subheader da aba de Auditoria Logística: `🚚 Auditoria de Comprovantes Logísticos`
  - Expander de Canhotos: `🔍 Auditar Canhotos de Viagens (Transportadoras)`
  - Expander de Liquidação de Boletos: `💸 Efetuar Liquidação de Boleto / Pagar Fornecedores (Em Lote)`

* **Botões de Ação:**
  - Confirmação de baixa de contas a pagar: `💸 Confirmar Baixa em Lote`
  - Confirmação de liquidação de contas a receber: `💸 Confirmar Recebimento em Lote`
  - Ação de Transferência: `🔄 Transferência entre contas` (alterado para `Transferência`)
  - Ação de Ajuste de Saldo: `🔧 Ajustar saldos` (alterado para `Ajustar saldo`)

* **Gráficos e Tabelas:**
  - Gráfico de Projeção 14D: `💰 Saldo Acumulado` (legenda do traço)
  - Tabela de Caixas e Bancos: `Revisado ✅` (título da coluna de conciliação)
  - Texto de prévia de duplicatas: `💰 **Total a ser lançado:**`

* **Alertas e Mensagens de Feedback:**
  - Mensagens de Sucesso (`st.success`): `✔️` (ex: "✔️ Ajuste de saldo registrado...")
  - Mensagens de Erro (`st.error`): `❌` (ex: "❌ Não é permitido cancelar...")
  - Mensagens de Aviso (`st.warning` / `st.markdown`): `⚠️` (ex: "⚠️ Gravação em andamento...", "⚠️ Tem certeza...")
  - Título do modal de bloqueio: `Lançamento Direto Bloqueado 🔒`
