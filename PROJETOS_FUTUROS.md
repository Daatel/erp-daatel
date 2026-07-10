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

## 📋 Kanban de Pedidos (Produção) - Repasse Horta do Príncipe
- **Objetivo:** Implementar o Kanban interativo (drag-and-drop) de pedidos de produção baseado na especificação `MD_Kanban_de_pedidos.MD` e no mockup `kanban_pedidos_producao_v3.html`.
- **Escopo Técnico:** Requer a criação de novas colunas e tabelas no Supabase (`data_prevista`, `grade_id`, etc.), configuração de Edge Functions (`mover-pedido`) para gerenciar as permissões e atualização de banco, e injeção do componente de interface Kanban no front-end Streamlit utilizando JavaScript vanilla e SortableJS.
- **Status:** Arquivado para o futuro devido ao elevado esforço técnico (estimativa de 4 a 6 horas) envolvendo manipulação simultânea de SQL, Serverless Functions (Deno) e integrações reativas de Front-end com JWT auth.


## 📋 Kanban de Pedidos (Produção) - Repasse Horta do Príncipe
- **Objetivo:** Implementar o Kanban interativo (drag-and-drop) de pedidos de produção baseado na especificação `MD_Kanban_de_pedidos.MD` e no mockup `kanban_pedidos_producao_v3.html`.
- **Escopo Técnico:** Requer a criação de novas colunas e tabelas no Supabase (`data_prevista`, `grade_id`, etc.), configuração de Edge Functions (`mover-pedido`) para gerenciar as permissões e atualização de banco, e injeção do componente de interface Kanban no front-end Streamlit utilizando JavaScript vanilla e SortableJS.
- **Status:** Arquivado para o futuro devido ao elevado esforço técnico (estimativa de 4 a 6 horas) envolvendo manipulação simultânea de SQL, Serverless Functions (Deno) e integrações reativas de Front-end com JWT auth.


## Transicao para Arquitetura SaaS (Longo Prazo)
- **Objetivo:** Refatorar o ERP monolito atual para uma arquitetura Multi-Tenant escalavel na nuvem.
- **Motivacao:** A arquitetura atual (Streamlit + Banco Flat) atende perfeitamente a uma operacao single-company, mas estruturalmente obriga adocao de dividas tecnicas (como agrupar multiplos itens em registros de vendas individuais). Para suportar multiplas empresas (SaaS) no futuro, o sistema inteiro precisa ser repensado do zero.
- **Arquitetura Proposta:**
  - **Banco de Dados:** Migracao para PostgreSQL Multi-Tenant (utilizando Row-Level Security com tenant_id em todas as tabelas) e separacao estrutural de vendas (cabecalho) e itens_venda (detalhes).
  - **Backend:** Separacao do front-end e criacao de uma API robusta em FastAPI (Python) ou Node.js para regras de negocio e integracoes pesadas.
  - **Frontend:** Substituicao do Streamlit por um framework SPA moderno (React/Next.js ou Vue.js), proporcionando interfaces assincronas de alta performance para dezenas de usuarios concorrentes.
  - **Infraestrutura:** Hospedagem baseada em containers (Docker/Kubernetes) ou arquitetura Serverless para escalar automaticamente durante picos de faturamento no final do mes.
- **Status:** Decisao estrategica registrada. Sera executada quando o produto evoluir para modelo SaaS comercial.

---

## 📊 Redesenho do Cockpit Financeiro Diário (Projeção vs Fechamento)
- **Objetivo:** Reformular o painel executivo diário para separar a rotina em duas visões complementares (Projeção Financeira do Dia & Fechamento Financeiro do Dia), com identidade visual sóbria, sem emojis e com foco em usabilidade.
- **Requisitos de Negócio e UX mapeados:**
  1. **Migração de Banco de Dados:** Adicionar a coluna `limite_credito` (NUMERIC/DECIMAL, default `0.0`) na tabela `contas_bancarias` (SQLite e PostgreSQL) e suportar sua edição na tela de Cadastros.
  2. **Exigência de Conciliação Matinal:** Exibir o aviso `⚠️ Relatório Requer Posições Conciliadas` na visão de Projeção caso existam lançamentos não conciliados de dias anteriores, orientando o usuário a conciliar antes de projetar.
  3. **Limite de Crédito Transparente:** Adicionar coluna de Limite de Crédito nas tabelas de saldo, sem somá-lo ao saldo líquido geral.
  4. **Aging de Atrasados:** Exibir em linha separada o aging de inadimplência acumulada (`0-30` / `31-60` / `60+` dias) para receber e pagar.
  5. **Plano de Contas Integrado:** Exibir e agrupar duplicatas com seu respectivo Plano de Contas (código e nome) e destacar lançamentos sem classificação (`Sem categoria — classificar` em vermelho).
  6. **Gráfico de Fluxo de Caixa Projetado:** Linha de saldo futuro acumulado e barras de entradas/saídas projetadas para os próximos 30 dias (em vez de histórico passado).
  7. **Fechamento Diário em PDF:** Botão na visão de Fechamento para emitir um relatório A4 corporativo limpo do dia realizado.
- **Status:** Planejado para futura implementação baseando-se nas especificações de `spec_mvp_financeiro.md` e `MD_Painel_Financeiro.md`.
