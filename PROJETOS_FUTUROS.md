# 🚀 Projetos Futuros & Roadmap ERP do Alho

Este documento registra as ideias, necessidades e módulos planejados para futuras iterações do sistema ERP da Fábrica de Alho.

---

## 📈 1. Painel Comercial (BI de Vendas)
* **Objetivo:** Criar um ambiente completo de Business Intelligence (BI) voltado para o time comercial e representantes de vendas.
* **Escopo:**
  * Substituir a visualização de abas gerais (como Painel Executivo, Ativos, Pessoas e Estoque) por um cockpit unificado de performance comercial.
  * Gráficos dinâmicos de faturamento por representante, evolução mensal de metas, ranking de produtos mais vendidos e clientes inativos.
  * Indicadores de positivação de carteira de clientes.
* **Público-alvo:** Perfil de acesso `VENDAS` (Comercial / Rotas).

---

## 💰 2. Painel Financeiro (BI Financeiro Operacional)
* **Objetivo:** Criar um ambiente de Business Intelligence (BI) focado na operação financeira diária e fluxo de caixa.
* **Escopo:**
  * Substituir a visualização de abas estratégicas (como DRE, Lucratividade e Rentabilidade por Cliente) por um cockpit focado na saúde financeira e fluxo de caixa operacional.
  * Indicadores visuais de contas a pagar e receber, taxa de inadimplência de boletos, conciliação bancária simplificada e previsibilidade de saldo de caixa.
* **Público-alvo:** Perfil de acesso `FINANCEIRO` (Tesouraria).

---

## 👑 3. Reforma do Painel Executivo (CEO Cockpit)
* **Objetivo:** Transformar o atual Dashboard em uma central de inteligência estratégica para o gestor geral / CEO.
* **Escopo:**
  * Agregar os dados consolidados de todas as áreas (DRE, Rentabilidade Geral, EBITDA, Margem de Contribuição, Evolução de Estoque Ativo, Lucratividade Líquida e Comissões a Pagar).
  * Exclusividade de acesso: Apenas o perfil `ADMIN` terá acesso a este painel altamente sensível e estratégico.
* **Público-alvo:** Perfil de acesso `ADMIN` (Diretoria / Gestão Geral).

---

## 🤖 4. Agente Cognitivo via Telegram (Assistente Administrativo Autônomo)
* **Objetivo:** Transformar o Bot do Telegram em uma interface bidirecional e ativa, capaz de receber comandos, fotos e áudios para operar o ERP de forma automática e inteligente.
* **Escopo:**
  * **Input por Imagem (OCR/LLM):** Upload de fotos de notas fiscais, boletos, comprovantes de pagamento ou fichas de cadastro de clientes. O Agente extrai os dados estruturados e realiza a inserção/cadastro automático no banco de dados.
  * **Input por Áudio (Speech-to-Text/LLM):** Envio de notas de voz de representantes e operadores na estrada (ex: lançando pedidos de venda ou apontamentos de fábrica por áudio). A IA transcreve, interpreta a intenção e executa a transação.
  * **Feedback Interativo:** Confirmações detalhadas de lançamentos e alertas educativos diretos no chat privado do usuário.
* **Público-alvo:** Diretoria, Equipe Administrativa, Representantes de Venda (Comercial) e Operadores de Fábrica.

---

## 👥 5. Módulo de Recursos Humanos Avançado (Fases 3, 4 e 5)
* **Objetivo:** Expandir o módulo Pessoas para um sistema completo de gestão de RH, incluindo controle de férias, cálculo de rescisões e integração com o sistema de pagamento bancário (CNAB).
* **Escopo:**
  * **Controle de Férias:** Rastreamento automatizado de períodos aquisitivos e concessivos de férias para funcionários CLT. Alertas visuais e jobs para notificar férias vencidas ou próximas do vencimento (evitando multas de férias em dobro). Tabela de redução de férias por faltas injustificadas.
  * **Cálculo Rescisório Automático:** Motor para cálculo de verbas rescisórias conforme tipo de desligamento (sem justa causa, com justa causa, pedido de demissão, acordo mútuo). Geração do Termo de Rescisão de Contrato de Trabalho (TRCT) com provisões de 13º proporcional, férias proporcionais + 1/3, aviso prévio e multa do FGTS (40% ou 20%).
  * **Exportação CNAB 240 / Lote PIX:** Geração de arquivos de remessa bancária no padrão FEBRABAN para pagamentos em lote de salários e benefícios, além de suporte a lotes de pagamento PIX via JSON API.
  * **Tabelas Fiscais Dinâmicas:** Migração das faixas e alíquotas de INSS, IRRF e salário mínimo para tabelas do banco de dados, permitindo a atualização anual de tributos via tela administrativa do gestor, sem necessidade de deploy de código.
* **Público-alvo:** Perfis `ADMIN` e `FINANCEIRO` (Recursos Humanos e Diretoria).

