# ?? Projetos Futuros & Roadmap ERP do Alho

Este documento registra as ideias, necessidades e módulos planejados para futuras iterações do sistema ERP da Fábrica de Alho.

> **Critério de priorização:** Projetos são ordenados por impacto operacional imediato × custo de implementação, não por sofisticação técnica. Iniciativas que reduzem esforço diário de todos os usuários precedem expansões funcionais que beneficiam poucos.

---

## P1 — Produtividade Operacional
> **Meta:** Reduzir cliques, erros e tempo de treinamento. Esses projetos afetam praticamente todos os usuários todos os dias.

---

### ??? 1. Central de Trabalho *(NOVO)*

* **Objetivo:** Transformar o ERP em um sistema orientado a tarefas, eliminando a necessidade do usuário "caçar" o que precisa fazer.
* **Escopo:**
  * Painel unificado de pendências por perfil de acesso, exibindo automaticamente o que requer ação do usuário.
  * Exemplos de cards por área:
    * Notas fiscais aguardando lançamento
    * Boletos aguardando pagamento
    * Depósitos aguardando conciliação
    * Pedidos aguardando faturamento
    * Rotas aguardando fechamento
  * Cada card é clicável e leva diretamente ao registro correspondente.
* **Impacto:** Altíssimo — reduz navegação, erros por esquecimento e tempo de treinamento de novos usuários.
* **Complexidade:** Média
* **Público-alvo:** Todos os perfis.

---

### ?? 2. Cadastro Inteligente

* **Objetivo:** Eliminar digitação manual e erros de cadastro via automação por API pública.
* **Escopo:**
  * Preenchimento automático de cadastro de **clientes** por CNPJ (Receita Federal).
  * Preenchimento automático de cadastro de **fornecedores** por CNPJ.
  * Preenchimento automático de **endereços** por CEP (ViaCEP).
  * Validação de CNPJ/CPF em tempo real na interface.
* **Impacto:** Muito Alto
* **Complexidade:** Baixa
* **Público-alvo:** Todos os perfis com acesso a cadastros.

---

### ?? 3. Lançamento Inteligente de NF

* **Objetivo:** Evoluir o recebimento fiscal de digitação manual para conferência assistida.
* **Escopo:**
  * Upload de XML da NF-e diretamente na tela de recebimento.
  * Conferência automática de itens, quantidades e valores contra o pedido de compra vinculado.
  * Validação de preços: alerta quando o preço da nota diverge do custo histórico ou do pedido.
  * Validação de prazo: verificação dos vencimentos dos títulos gerados contra o que foi negociado.
  * Sugestão automática de cadastro de novos produtos ou fornecedores detectados no XML.
* **Impacto:** Muito Alto
* **Complexidade:** Média
* **Público-alvo:** Perfil `FINANCEIRO` e `ADMIN`.

---

### ?? 4. Conciliação Bancária Assistida

* **Objetivo:** Substituir a conciliação manual por um fluxo semi-automático onde o usuário valida exceções, não executa o processo inteiro.
* **Escopo:**
  * Importação de extrato bancário (OFX/CSV).
  * Motor de sugestão automática: o ERP associa cada lançamento do extrato ao registro interno mais provável (boleto, pagamento, transferência).
  * O usuário revisa apenas os lançamentos não associados automaticamente.
  * Geração de relatório de conciliação com aprovação por usuário responsável.
* **Impacto:** Muito Alto — base de qualidade para qualquer BI financeiro futuro.
* **Complexidade:** Média
* **Público-alvo:** Perfil `FINANCEIRO`.

---

### ?? 5. Painel Operacional do Dia *(NOVO)*

* **Objetivo:** Dar ao gestor uma visão consolidada do dia em menos de 10 segundos.
* **Escopo:**
  * Widget na tela inicial (por perfil) com os números mais críticos do dia corrente.
  * Exemplos de indicadores:
    * Pagamentos com vencimento hoje
    * Cobranças previstas para hoje
    * Pedidos em aberto aguardando faturamento
    * Pendências financeiras não resolvidas
  * Design minimalista, sem necessidade de navegação para acessar.
* **Impacto:** Alto
* **Complexidade:** Baixa
* **Público-alvo:** Perfis `ADMIN` e `FINANCEIRO`.

---

## P2 — Inteligência Operacional
> **Meta:** Fazer o ERP ajudar a decidir, não apenas registrar.

---

### ?? 6. Painel Comercial (BI de Vendas)

* **Objetivo:** Criar um ambiente completo de Business Intelligence voltado para o time comercial e representantes de vendas.
* **Escopo:**
  * Substituir a visualização de abas gerais por um cockpit unificado de performance comercial.
  * Gráficos dinâmicos de faturamento por representante, evolução mensal de metas, ranking de produtos mais vendidos e clientes inativos.
  * Indicadores de positivação de carteira de clientes.
* **Dependência:** Funciona melhor após a Central de Trabalho e o Cadastro Inteligente estabilizarem a qualidade dos dados comerciais.
* **Público-alvo:** Perfil `VENDAS` (Comercial / Rotas).

---

### ?? 7. Painel Financeiro (BI Financeiro Operacional)

* **Objetivo:** Criar um ambiente de Business Intelligence focado na operação financeira diária e fluxo de caixa.
* **Escopo:**
  * Cockpit focado na saúde financeira e fluxo de caixa operacional.
  * Indicadores visuais de contas a pagar e receber, taxa de inadimplência de boletos e previsibilidade de saldo de caixa.
  * **Previsão de Fluxo de Caixa** em 30, 60 e 90 dias com base em títulos em aberto e histórico de recebimentos.
* **Dependência:** Requer Conciliação Bancária Assistida (P1.4) em operação. BI financeiro sobre dados não conciliados gera relatórios não confiáveis.
* **Público-alvo:** Perfil `FINANCEIRO` (Tesouraria).

---

### ?? 8. Reforma do Painel Executivo (CEO Cockpit)

* **Objetivo:** Transformar o atual Dashboard em uma central de inteligência estratégica para o gestor geral / CEO.
* **Escopo:**
  * Agregação de dados consolidados de todas as áreas: DRE, Rentabilidade Geral, EBITDA, Margem de Contribuição, Evolução de Estoque Ativo, Lucratividade Líquida e Comissões a Pagar.
  * Exclusividade de acesso: apenas perfil `ADMIN`.
  * **Análise por Região (Geográfica):** Integração do campo **Região** no cadastro de clientes, contemplando as 10 macro-regiões de atendimento (*Centro/Sul, Norte, Oeste, Sudoeste, Baixada, Niterói/S. Gonçalo, Lagos, N. Fluminense, S. Fluminense e Costa Verde*), permitindo agrupamento de faturamento, positivação e rentabilidade geográfica.
  * **Rentabilidade Geográfica:** Receita, margem, positivação e ticket médio por região.
* **Dependência:** Requer Painéis Comercial (P2.6) e Financeiro (P2.7) como base de dados.
* **Conceito Visual Desenvolvido:**
  ![Conceitos do BI Painel Executivo](PAINEL%20EXECUTIVO.png)
* **Público-alvo:** Perfil `ADMIN` (Diretoria / Gestão Geral).

---

### ?? 9. CNAB 240 / PIX em Lote *(reposicionado do P4)*

* **Objetivo:** Automatizar pagamentos em lote de fornecedores, salários e benefícios via integração bancária.
* **Escopo:**
  * Geração de arquivos de remessa bancária no padrão FEBRABAN (CNAB 240) para pagamentos em lote.
  * Suporte a lotes de pagamento PIX via JSON API.
  * Conciliação automática dos pagamentos confirmados pelo banco.
* **Nota:** Projeto financeiro, não de RH — o benefício se estende a pagamentos de fornecedores e qualquer saída em lote, não apenas folha.
* **Público-alvo:** Perfil `FINANCEIRO` e `ADMIN`.

---

### ?? 10. Sistema de Alertas Inteligentes *(NOVO)*

* **Objetivo:** Fazer o ERP notificar proativamente, sem que o usuário precise consultar relatórios.
* **Escopo:**
  * Motor de regras configurável pelo administrador.
  * Exemplos de alertas:
    * Cliente X dias sem realizar compra
    * Estoque abaixo do ponto de reposição
    * Férias vencendo nos próximos Y dias
    * Conta bancária sem conciliação há Z dias
    * Boleto vencido sem baixa
  * Entrega via interface do ERP (notificação interna) e, futuramente, via Telegram/WhatsApp.
* **Público-alvo:** Todos os perfis (alertas segmentados por perfil).

---

## P3 — Automação e IA
> **Meta:** Fazer o ERP executar tarefas, não apenas informar.

---

### ?? 11. Assistente Operacional IA *(anteriormente: Agente Cognitivo Telegram)*

* **Objetivo:** Transformar o Bot do Telegram em uma interface bidirecional e ativa, capaz de receber comandos, fotos e áudios para operar o ERP de forma automática e inteligente.
* **Escopo:**
  * **Input por Áudio (Speech-to-Text/LLM):** Notas de voz de representantes e operadores. A IA transcreve, interpreta a intenção e executa a transação (ex: lançar pedido de venda por áudio).
  * **Feedback Interativo:** Confirmações detalhadas de lançamentos e alertas proativos no chat do usuário.
* **Nota sobre nomenclatura:** O nome "Assistente Operacional IA" foi adotado intencionalmente. A inteligência é mais importante que o canal de entrega — futuramente pode operar via Telegram, WhatsApp, app próprio ou portal web.
* **Público-alvo:** Diretoria, Equipe Administrativa, Representantes de Venda e Operadores de Fábrica.

---

### ?? 12. Processamento de Documentos por IA *(NOVO — separado do Assistente)*

* **Objetivo:** Extrair dados estruturados de documentos físicos ou digitais enviados pelo usuário, eliminando digitação manual.
* **Escopo:**
  * **Input por Imagem (OCR/LLM):** Upload de fotos de notas fiscais, boletos, comprovantes de pagamento ou fichas de cadastro. O sistema extrai dados e realiza inserção/cadastro automático no banco de dados.
  * Entradas suportadas: Nota Fiscal (papel ou PDF), boleto bancário, comprovante de pagamento/transferência, ficha de cadastro de cliente.
  * Saída: dados estruturados, sugestão de cadastro, lançamentos prontos para aprovação do usuário.
* **Nota:** Separado do Assistente Operacional por ser um projeto técnico independente (pipeline OCR + LLM + validação), com lógica e equipe distintas.
* **Público-alvo:** Equipe Administrativa, Financeiro e Representantes de Venda.

---

### ??? 13. ERP Conversacional *(NOVO)*

* **Objetivo:** Permitir que o usuário consulte o ERP em linguagem natural, sem precisar navegar por relatórios.
* **Escopo:**
  * Barra de busca inteligente acessível de qualquer tela.
  * Exemplos de consultas:
    * *"Quanto vendi para o cliente X este mês?"*
    * *"Quais clientes estão sem comprar há mais de 30 dias?"*
    * *"Qual foi minha margem de contribuição ontem?"*
    * *"Qual o saldo atual da conta Bradesco?"*
  * Respostas em linguagem natural com opção de abrir o relatório completo correspondente.
* **Dependência:** Requer qualidade de dados garantida pelas iniciativas de P1 e P2.
* **Público-alvo:** Perfis `ADMIN`, `FINANCEIRO` e `VENDAS`.

---

### ??? 14. Operação por Voz *(NOVO)*

* **Objetivo:** Permitir o registro de pedidos e apontamentos por comando de voz, especialmente para representantes em campo.
* **Escopo:**
  * Representante fala: *"Pedido para Supermercado Silva: 10 caixas de produto A, 5 de produto B."*
  * Sistema transcreve, interpreta e gera o rascunho do pedido para confirmação.
  * Integrado ao Assistente Operacional IA (P3.11).
* **Público-alvo:** Representantes de Venda (Comercial / Rotas).

---

## P4 — Expansão Corporativa
> **Meta:** Tornar o ERP mais completo para gestão de pessoas e compliance trabalhista.

---

### ?? 15. Módulo de Recursos Humanos Avançado (Fases 3, 4 e 5)

* **Objetivo:** Expandir o módulo Pessoas para um sistema completo de gestão de RH.
* **Escopo:**
  * **Controle de Férias:** Rastreamento automatizado de períodos aquisitivos e concessivos. Alertas visuais e jobs para notificar férias vencidas ou próximas do vencimento (evitando multas de férias em dobro). Tabela de redução de férias por faltas injustificadas.
  * **Cálculo Rescisório Automático:** Motor para cálculo de verbas rescisórias conforme tipo de desligamento (sem justa causa, com justa causa, pedido de demissão, acordo mútuo). Geração do TRCT com provisões de 13º proporcional, férias proporcionais + 1/3, aviso prévio e multa do FGTS (40% ou 20%).
  * **Tabelas Fiscais Dinâmicas:** Migração das faixas e alíquotas de INSS, IRRF e salário mínimo para tabelas do banco de dados, permitindo atualização anual via tela administrativa sem deploy de código.
* **Nota:** O módulo de CNAB/PIX em Lote foi reposicionado para P2 por ser um projeto financeiro com escopo mais amplo que RH.
* **Público-alvo:** Perfis `ADMIN` e `FINANCEIRO` (Recursos Humanos e Diretoria).

---

### ? 16. Módulo de Controle de Ponto Eletrônico (Portaria 671/2021)

* **Objetivo:** Integrar um sistema de controle de ponto eletrônico digital e homologado para os colaboradores da fábrica.
* **Escopo:**
  * **API de Ponto (FastAPI):** Registro de batidas com detecção inteligente de tipo (Entrada, Saída, Intervalo), cálculo em tempo real de horas trabalhadas no dia e suporte a registros temporários offline.
  * **Terminal de Batida Kiosk (Tablet):** Interface web otimizada para tablets na recepção da fábrica, permitindo batida de ponto via QR Code do crachá (câmera integrada com jsQR) ou PIN numérico individual de 4 dígitos.
  * **Relatório de Espelho de Ponto:** Geração automática e exportação do histórico mensal detalhado para assinatura do colaborador, em conformidade com as diretrizes do MTE.
* **Público-alvo:** Todos os colaboradores (CLT e Diaristas) e equipe de RH/Diretoria.

---

## Projetos Adicionais Identificados

> Iniciativas de alto valor estratégico ainda sem fase definida. Serão incorporadas ao roadmap conforme maturidade operacional das fases anteriores.

---

### ?? Planejamento de Compras *(NOVO)*

* **Objetivo:** Substituir a compra por intuição por sugestões baseadas em dados.
* **Escopo:**
  * Sistema de sugestão de compras com base em estoque atual, histórico de consumo e previsão de produção.
  * Geração de rascunho de pedido de compra para aprovação do gestor.

---

### ??? Rentabilidade Geográfica *(NOVO)*

* **Objetivo:** Mostrar onde o negócio é mais e menos lucrativo geograficamente.
* **Escopo:**
  * Aproveitamento do campo Região já previsto no Painel Executivo (P2.8).
  * Indicadores por região: Receita, Margem de Contribuição, Positivação de Carteira e Ticket Médio.
  * Identificação de regiões com queda de performance para ação comercial direcionada.

---

*Documento mantido como referência viva. Revisão recomendada a cada trimestre ou após conclusão de fase.*

