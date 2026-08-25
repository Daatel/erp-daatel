# 📋 Histórico de Versões — ERP Fábrica de Alho

---

## v2.0 — 2026-08-25 (Sessão: Conector de Voz ERP DAATEL via Telegram Bot & IA Gemini NLU)

### 🎙️ Conector de Voz & Telegram Bot (`telegram_bot_listener.py`, `services/`)
- **Long Polling & Event Loop Async:** Servidor `telegram_bot_listener.py` assíncrono escutando o bot `@Daatel_Agente_bot` com scheduler de limpeza TTL (24h) e trava atômica por `rowcount == 1`.
- **Engine Gemini API NLU (`services/voice_nlu_service.py`):** Transcrição e estruturação inteligente de comandos de voz em 4 modos (`PDV_EXPRESS`, `PEDIDO_VENDA`, `CONTA_PAGAR`, `CONTA_RECEBER`) com expurgo remoto de mídia temporária via `genai.delete_file` (LGPD).
- **Busca Fuzzy & Entidades (`services/voice_entity_matcher.py`):** Algoritmo de cruzamento fonético insensível a acentuação e caixa para Clientes, Fornecedores, Produtos e Plano de Contas.
- **Emissão Instantânea de DAV em PDF (`services/voice_pdf_service.py`):** Geração de Documentos Auxiliares de Venda em PDF ReportLab enviados diretamente no Telegram via `sendDocument`.
- **Resolução Estrita de Pagamentos & Contas (`services/erp_voice_bridge.py`):** Direcionamento obrigatório de *Dinheiro* para a conta **Caixa Físico** e *Pix* para a conta **Banco Bradesco**. Botões inline interativos quando o meio é omitido.
- **Resolução de Clientes e Prazos:** Suporte a Pedidos de Venda com cálculo de prazo de vencimento herdado do cadastro do cliente ou dito no áudio, e menu interativo `[🔍 Escolher da Lista]` ou fallback para `CONSUMIDOR FINAL / BALCÃO`.

### 👥 Módulo de Pessoas & Configurações (`pages/3_Pessoas.py`, `database.py`)
- **Integração de Telegram Chat ID:** Novos campos `Telegram Chat ID` e `Limite de Alçada por Voz (R$)` adicionados ao **Bloco 6: Ferramentas, Acessos e Termos de Aceite** dos formulários de cadastro e edição de colaboradores em `3_Pessoas.py`.
- **Migrations DDL (SQLite/PostgreSQL):** Criação das tabelas `telegram_usuarios_autorizados`, `rascunhos_voz_telegram` e `audit_log_voz` com suporte a `TIMESTAMP` e seed idempotente `CONSUMIDOR`.

---

## v1.9.5 — 2026-08-18 (Sessão: Otimização do Financeiro — Contas a Pagar/Receber, Dt. Emissão, Plano de Contas & Grids Interativas)

### 💵 Reestruturação de Contas a Pagar & Receber (`pages/9_Financeiro.py`, `utils_financeiro_modals.py`)
- **Campo Data de Emissão (`data_emissao`):** Adicionado suporte completo à Data de Emissão original da NF/Título nos formulários e relatórios do Contas a Pagar e Receber.
- **Busca Flexível Cliente/Fornecedor:** Busca padrão configurada por Nome Fantasia com opção de alternância por checkbox para Razão Social.
- **Tratamento de Dados Legados & N. Doc:** Limpeza dinâmica de Número do Documento, resolução automática de Plano de Contas omisso em títulos legados e vinculação estrita à Conta Bancária.
- **Grids Interativas & Regra Anti-Banheira:** Migração das grids de liquidação/baixas para `st.dataframe` com seleção nativa, ordenação SQL determinística por `id ASC` e congelamento imediato de seleção em `st.session_state`.
- **Ajuste de Saldo Bradesco (31/07/2026):** Lançamento automático e idempotente de ajuste de saldo na conta Bradesco fixado em R$ 1.961,54.

### 🗄️ Banco de Dados & DDL (`database.py`)
- **Migração DDL Automatizada (SQLite/PostgreSQL):** Automação de `ALTER TABLE` para inclusão da coluna `data_emissao` compatível com PostgreSQL (Supabase) e SQLite.

---

## v1.9 — 2026-08-04 (Sessão: Conciliador Bancário Inteligente OFX, Relatório Razão & Ajustes de Tesouraria)

### 🔄 Conciliador Bancário Automático OFX (`utils_ofx.py`, `pages/9_Financeiro.py`)
- **Parser SGML/XML Resiliente:** Leitor em Python puro para arquivos `.ofx` compatível com Bradesco, Itaú, Banco do Brasil, Caixa e bancos digitais.
- **Matching com Consumo de Pool:** Motor de busca que associa títulos do Contas a Pagar/Receber mantendo estado por sessão, evitando que dois lançamentos de mesmo valor no mesmo dia sintonizem com o mesmo título.
- **Tolerância Estrita D-2:** Filtro de vencimento limitado a até 2 dias de diferença. Lançamentos mais distantes exigem validação manual humana.
- **Transação Atômica ACID:** Processamento em lote envolvido em `BEGIN / COMMIT / ROLLBACK` atômico via `db_transaction()`. Se um item falhar, nenhuma alteração é persistida no banco.
- **Modo Simulação (Dry Run):** Opção de teste em tela para validar o matching sem gravar no banco de dados.
- **Design de Interface Limpo:** Aplicação de estilo CSS customizado para o `stFileUploader` (removendo fundo escuro) e padronização tipográfica do cabeçalho de conciliação.

### 📄 Relatório Razão / Extrato de Caixas e Bancos (`pages/9_Financeiro.py`)
- **Extrato Diário em PDF:** Botão `📄 Extrato / Razão` na aba Caixas e Bancos gerando relatório em PDF segregado por dia com Saldo Inicial, Histórico, Plano de Contas, Entradas, Saídas e Saldo Final de cada dia.
- **Cálculo Retroativo de Saldo Inicial:** Apuração de saldo acumulado anterior à data inicial do período (`< dt_ini`), com suporte a relatórios por conta individual ou consolidado ("Todas as contas").
- **Dica de Interface:** Exibição de nota explicativa esclarecendo a composição de saldos consolidados entre Bradesco e Caixa Físico.

### 🗄️ Tesouraria & Banco de Dados (`database.py`, `pages/9_Financeiro.py`)
- **Trava Anti-Duplicidade:** Adicionada a coluna `fitid TEXT` e índice `idx_fluxo_caixa_fitid` na tabela `fluxo_caixa`.
- **Ajuste de Saldo Bradesco:** Ajustado o saldo acumulado do Bradesco em 30/06/2026 para R$ 719,33, alinhando a abertura de conciliação em 01/07/2026 com o extrato bancário real.
- **Correção de Arredondamento:** Corrigido o modal de ajuste de saldo para arredondar a diferença em 2 casas decimais (`round(..., 2)`).
- **Saneamento de Lançamento:** Excluída a duplicata do Contas a Pagar (ID 54 / Fluxo ID 57) relativa à compra de bomba nova Masterson.

---

## v1.8 — 2026-07-25 (Sessão: Reformulação do Módulo de Produção — Seleção, Metas e Rendimento de Alho)

### 🧄 Novo Módulo de Seleção e Pesagem (`components/selecao/` e `pages/4_Producao.py`)
- **Arquitetura Modular:** Módulo de produção reestruturado em componentes isolados (`components/selecao/`), englobando BI, Mesa de Seleção, Ranking, Configurações e PDF.
- **Painel BI de Seleção (`painel_bi.py`):** Visualização executiva de indicadores mensais, gráfico diário de produção vs. meta da casa e projeção de entregas.
- **Mesa de Seleção Operacional (`mesa.py`):** Lançamento simplificado de presença diária, pesagem individual por selecionadora e registro de rendimento por lote (Nobre, 2ª Linha e Descarte).
- **Ranking de Selecionadoras (`ranking.py`):** Tabela de performance filtrada pelo cargo Selecionador(a), comparando pesagem realizada contra meta individual.
- **Gerenciamento de Metas & Calendário (`configuracoes.py`):** Definição de metas por nível (A/B/Teste), parâmetros mensais e calendário de exceções/feriados.
- **Folha de Pesagem em PDF (`pdf_folha.py`):** Exportação em PDF formatado com ReportLab para preenchimento ou arquivamento físico.

### 🗄️ Banco de Dados & Pessoas (`pages/3_Pessoas.py`, `database.py`)
- **Perfil de Selecionadora:** Adicionado cargo "Selecionador(a)" no cadastro de pessoas com definição de Nível de Classificação (`A`, `B`, `Teste`) e Vínculo (`CLT`/`Diarista`).
- **Migração SQL Integrada (`migration_selecao.sql`):** Persistência relacional completa para histórico de níveis, pesagens diárias e aproveitamento de lotes.

---

## v1.7 — 2026-06-18 (Sessão: Desacoplamento de Estorno e Correção de Emissão de DAV)

### ✅ Tela de Faturamento Independente (`7_Faturamento.py`)
- **Visualização sempre ativa:** O painel expansível de reimpressão de documentos (DAVs/NFs) agora fica sempre visível no faturamento, mesmo quando a fila de pedidos aprovados pendentes estiver vazia.
- **Evitado cache de imports:** Adicionado recarregamento dinâmico via `importlib.reload(utils_dav)` para contornar caches de importação no Streamlit, garantindo que alterações no arquivo de utilitário entrem em vigor imediatamente.

### ✅ Nova aba "Estornar NF / DAV" (`7_Faturamento.py`)
- **Segregação de UX:** Movido todo o fluxo de cancelamento/estorno de faturamentos (Central de Segurança) para uma nova aba dedicada na tela de faturamento, evitando que o usuário confunda a ação de impressão com a de cancelamento.
- **Relatório de Sucesso Detalhado:** Ao concluir o estorno de uma venda/DAV, o sistema agora exibe um passo a passo detalhando as 3 ações atômicas realizadas:
  1. Que as mercadorias foram devolvidas ao estoque físico.
  2. Que o título do Contas a Receber foi excluído e as contas a pagar de comissão/taxa de descarga pendentes foram canceladas.
  3. Que o pedido retornou ao status comercial "APROVADO" para ser alterado, refaturado ou cancelado de vez nas vendas.

### ✅ Correção na Consulta de Emissão de DAV (`utils_dav.py`)
- **Fix de coluna de banco de dados:** Corrigida a consulta SQL de geração de dados da DAV para buscar `c.cnpj_cpf` (coluna real da tabela `clientes`) em vez de `c.cnpj` (coluna inexistente), sanando o erro que impedia a visualização da folha A4 e a impressão do documento no Streamlit Cloud.

---

## v1.6 — 2026-06-12 (Sessão: Integridade Financeira e Paridade NF × DAV)

### ✅ Inteligência de Baixa no Financeiro (`9_Financeiro.py`)
- **Descontos automáticos:** Quando o valor pago é inferior ao título original, o sistema lança automaticamente a diferença como **"Descontos Concedidos"** no fluxo de caixa, preservando o valor original da venda no DRE.
- **Acréscimos/Juros automáticos:** Quando o valor pago excede o título, a diferença é lançada como entrada adicional na categoria **"outros"** (juros/mora).
- **Restrição de edição direta:** Recebíveis vinculados a vendas (`venda_id NOT NULL`) não podem ter o valor alterado diretamente — a tela orienta para o módulo de Baixa ou Faturamento.
- **Bloqueio de exclusão:** Recebíveis ligados a vendas não podem ser excluídos/cancelados; a reversão deve ser feita pelo estorno de faturamento.

### ✅ DRE atualizado (`10_DRE.py`)
- Regex de deduções expandido para incluir `desconto` e `abatimento`, garantindo que descontos concedidos sejam corretamente abatidos da Receita Líquida.

### ✅ Paridade de Documento NF × DAV (`7_Faturamento.py`, `8_Logistica.py`)
- **Aviso contextual na Fila de Faturamento:** Ao selecionar o tipo de documento, exibe imediatamente o impacto no fluxo:
  - **DAV** → número gerado automaticamente, embarque liberado imediatamente.
  - **NF** → alerta de que o embarque ficará retido até o número SEFAZ ser registrado, com sugestão de usar DAV para embarque imediato.
- **Painel de dados de NF na Reimpressão:** Substituída a mensagem vazia por painel com todos os dados do registro (número, data, cliente, CNPJ/CPF, produto, quantidade, valor, lote e validade), além de estado do número SEFAZ com orientação contextual.
- **Mensagem orientativa na Logística:** Erro de embarque bloqueado por NF sem número SEFAZ agora lista as notas afetadas e oferece **2 caminhos claros**: registrar o número no Gerador Fiscal ou estornar e refaturar como DAV.

### 🗄️ Banco de Dados — sem alterações de schema
Todas as melhorias desta versão são de lógica de negócio e UX; nenhuma migração de banco foi necessária.

---



### 🚀 Banco de Dados Cloud (Supabase / PostgreSQL)
- **Migração Total:** Arquitetura do sistema refatorada de SQLite (local) para PostgreSQL via Supabase.
- Script automatizado de conversão de dados rodou com 100% de integridade (tipagem, conversões de booleanos e DDL sem Foreign Keys de travamento temporal).
- **Pool de Conexões:** Implementado `psycopg2.pool.SimpleConnectionPool` encapsulado com `@st.cache_resource`, zerando as falhas de latência (`Baiano com Dengue` issue) devido a handshakes repetitivos via TCP/IP na AWS.
- **Performance de DDL:** Removido o gargalo crônico do `create_tables()` a cada refresh no Streamlit, consolidando a persistência nativa.

### 🚀 Deploy Mundial (Streamlit Community Cloud)
- Código fonte estabilizado e vinculado ao **GitHub**.
- CI/CD básico implantado. Senhas secretas abstraídas via `.streamlit/secrets.toml`.
- **Acesso Público Multi-dispositivo:** O sistema é agora totalmente web, acessível por celulares e desktops externos.

---

## v1.4 — 2026-05-16 (Sessão: Homologação Nuvem & UX Single Task)

### ✅ Gestão de Ativos e Comodatos (`11_Ativos_Comodatos.py`)
- Módulo criado do zero para controle de freezers e equipamentos cedidos.
- **Farol de Rentabilidade (ROI)** cruzando Vendas Faturadas x Dias de Comodato.
- **Geração Dinâmica de Contratos em PDF** automatizada via `fpdf2`.

### ✅ Configurações da Empresa Dona do Sistema
- Aba "🏢 Minha Empresa" injetada em `1_Cadastros.py`.
- Nova tabela `empresa_config` centraliza CNPJ, Razão Social e Endereço para injeção automática em documentos fiscais e jurídicos.

### ✅ UX / Single Task e Navegação Segura
- **Streamlit 1.36+ `st.navigation`**: Roteamento reimplementado por cargos (ADMIN, VENDAS, PRODUCAO, FINANCEIRO).
- Remoção absoluta da barra lateral nativa garantindo que telas protegidas não fiquem visíveis na URL.
- Correção de injeção silenciosa de usuários no banco de dados SQLite (`fix_users.py`).

### ✅ UI React Fixes
- Remoção do bug `NotFoundError (removeChild)` em `6_Pedidos_de_Venda.py` substituindo reruns síncronos fora de formulários pelo sistema assíncrono de notificações (`st.toast`).

---

## v1.3 — 2026-05-11 (Sessão: JIT, Acordos Comerciais e Logística)

### ✅ Rastreabilidade de Lotes Just-In-Time (JIT)
- **Produção** (`4_Producao.py`): Lotes passam a ter **Data de Validade** além da Data de Fabricação
- **Estoque** (`5_Estoque.py`): Nova aba **"🕵️ Rastreabilidade (PEPS)"** — cálculo FIFO físico por lote
- **Faturamento** (`7_Faturamento.py`): Operador edita Lote + Validade no momento da expedição (JIT); impresso na NF/DAV sem travar estoque contábil

### ✅ Reestruturação de Comissões (RH)
- **Módulo de Vendas**: Removidas abas "Central de Comissões" e "Extrato Mensal do Vendedor"
- **Módulo de RH** (`3_Pessoas.py`): Ambas migradas — comissão é variável de folha pós-faturamento/liquidação

### ✅ Acordos Comerciais e Rebates de Rede
- **Tabelas de Preço**: 3 novos campos de rebate — `% Contrato`, `% Comissões Auxiliares`, `% Acordo Logístico`
- **Pedido de Venda**: Calcula e grava `custo_acordos_rede` no momento do pedido
- **Faturamento**: Gera **Contas a Pagar D+30** automaticamente para a rede
- **DRE**: Nova linha **"5.1 (-) Acordos Comerciais (Rebates de Rede)"**

### ✅ Taxas e Regras de Descarga por Cliente
- **Cadastro de Clientes**: Novos campos `Taxa de Descarga (R$)` e `Regras/Horários de Descarga`
- **Faturamento**: Gera **Contas a Pagar D+0** e grava `custo_descarga` na venda
- **Logística**: Alertas visuais na montagem do manifesto; Romaneio inclui taxa e regras para o motorista
- **DRE**: Nova linha **"5.2 (-) Taxas de Descarga (CD/Redes)"** — custo comercial variável correto

### ✅ Fluxo Documental Logística → Financeiro (Segregação de Responsabilidades)
- **Fechamento de Rota**: Exige dois uploads por entrega — 📄 Canhoto + 🧾 Recibo de Descarga
  - Upload salva comprovante; status da conta muda para `AGUARDANDO BAIXA`
  - Botão "Fechar Rota" bloqueado até todos os documentos estarem anexados
- **Financeiro**: Novo filtro `AGUARDANDO BAIXA`; expander de auditoria de recibos; baixa manual em lote
- **Regra:** somente o Financeiro dá a baixa — Logística só entrega os documentos digitalizados

### 🗄️ Banco de Dados — Novas Colunas (migração automática, sem perda de dados)
| Tabela | Novas Colunas |
|---|---|
| `producao_diaria` | `data_validade` |
| `vendas` | `lote_impresso`, `validade_impressa`, `custo_acordos_rede`, `custo_descarga` |
| `tabelas_preco` | `pct_contrato`, `pct_comissao_auxiliar`, `pct_acordo_logistico` |
| `clientes` | `taxa_descarga`, `regras_descarga` |
| `contas_a_pagar` | `comprovante_url` |

### 🏛️ DRE — Estrutura Final de Despesas Comerciais Variáveis
```
5.   (-) Comissões + Fretes rateados
5.1  (-) Acordos Comerciais (Rebates de Rede) D+30
5.2  (-) Taxas de Descarga CD/Redes           D+0
     ─────────────────────────────────────────────
(=)  MARGEM DE CONTRIBUIÇÃO LÍQUIDA
```

---

## v1.1 — 2026-05-04 (Sessão de Homologação — Fase 1 Concluída)

### ✅ Módulos Validados
- **Cadastros** (Produtos, Fornecedores, Clientes, Contas Bancárias)
- **Compras** (NFs de Entrada com multi-itens e créditos fiscais)
- **Estoque** (Posição, Alertas e Ajustes Manuais)
- **Financeiro — Contas a Pagar** (Liquidação em lote, Renegociação, Reparcelamento)

### 🔧 Compras (`2_Compras.py`)
- **Filtro inteligente de produtos por destino** — Produção mostra só matéria-prima; Revenda mostra só acabados
- **Cancelamento de NF** — Botão "❌ Cancelar/Estornar NF" com estorno completo (estoque + duplicatas + cabeçalho)
- **Auto-geração de duplicatas** — Parcelas criadas automaticamente pelo prazo do fornecedor ao adicionar itens
- **Histórico com vencimentos** — Tabela agora mostra coluna "Duplicatas" com datas, valores e status
- **Fix:** Removidas colunas ICMS/IPI inexistentes do formatador do histórico

### 🔧 Cadastros (`1_Cadastros.py`)
- **Edição expandida** — Formulário agora inclui "É Matéria-Prima?" (checkbox) e "Estoque Mínimo" (numérico)
- **Unidade de Compra** — Campo texto livre substituiu tipos fixos

### 🔧 Estoque (`5_Estoque.py`)
- **Checkbox "Mostrar produtos com estoque zerado"** — Oculta por padrão, exibe ao marcar

### 🔧 Financeiro (`9_Financeiro.py`)
- **Renegociação completa de duplicatas** com 3 opções:
  - Alterar Vencimento/Valor
  - Aplicar Juros (%) / Desconto (R$) com cálculo em tempo real
  - Reparcelar em N parcelas (cancela original, cria novas com preview)
- **Fix:** Dados de fornecedor e plano de custo preservados no reparcelamento

### 🗄️ Banco de Dados
- Tabela `compras_itens`: `produto_id` agora aceita NULL (consumo interno)
- Cartão Corporativo Itaú cadastrado como conta bancária

### 🛡️ Infraestrutura
- **Backup versionado** com `Backup_ERP.bat` (ZIPs datados no OneDrive, últimas 10 versões)
- **CHANGELOG.md** criado para rastrear alterações por versão

### 🚩 Próxima Sessão (Fase 2 e 3 do Checklist)
1. **Produção** — Iniciar lote diário, consumir matéria-prima, gerar produto acabado
2. **Vendas / Faturamento** — Registrar pedidos, gerar NFs de saída
3. **Financeiro — Contas a Receber** — Verificar duplicatas de clientes
4. **Fluxo de Caixa** — Validar entradas e saídas end-to-end

---

## v1.0 — 2026-05-04 (Backup: ERP_Backup_2026-05-04_003209.zip)

### 🔧 Correções e Melhorias no Módulo de Compras (`2_Compras.py`)
- **Data em formato brasileiro** (DD/MM/YYYY) no campo de data da compra
- **Formulário reativo** — removido `st.form`, cálculos de custo atualizam em tempo real
- **Consumo Interno** — campo de texto livre para itens que não são do catálogo (limpeza, escritório)
- **Reset de campos** — Custo Líq. Unitário zera corretamente a cada novo item
- **Gestão de Unidades** — campo "Unidade de Compra" entre Quantidade e Preço (Milheiro, Kg, Resma)
- **Conversão de Estoque** — sistema calcula automaticamente: 2 Milheiros = 2.000 unidades no estoque
- **Filtro inteligente de produtos** — destino "Produção" mostra só matéria-prima; "Revenda" mostra só acabados
- **Cancelamento de NF** — botão "❌ Cancelar/Estornar NF" com estorno completo (estoque + duplicatas + cabeçalho)
- **Histórico atualizado** — colunas de Unidade e Qtd Estoque no detalhamento de NF

### 🔧 Correções no Módulo de Cadastros (`1_Cadastros.py`)
- **Unidade de Compra** — campo de texto livre substituiu o antigo "Tipo de Embalagem" (SACO/CAIXA/UNIDADE)
- **Fator de Conversão** — rótulo mais claro com dica explicativa
- **Formulário de Edição expandido** — agora inclui 11 campos: Nome, Marca, Preço, Custo, Unidade de Compra, Fator de Conversão, Custo Fardo, Peso/Volume, Referência, **É Matéria-Prima** e **Estoque Mínimo**

### 🔧 Correções no Módulo de Estoque (`5_Estoque.py`)
- **Checkbox "Mostrar produtos com estoque zerado"** — oculta por padrão, exibe ao marcar

### 🔧 Correções no Módulo Financeiro (`9_Financeiro.py`)
- **Correção de IndentationError** no bloco de Fechamento de Carteira

### 🗄️ Banco de Dados (`database.py`)
- Tabela `compras_itens`: adicionadas colunas `unidade`, `quantidade_estoque`, `produto_nome`; `produto_id` agora aceita NULL (consumo interno)
- Migração automática para bancos existentes (ALTER TABLE com try/except)

### 📦 Dados de Teste
- 4 fornecedores ativos, 3 clientes ativos, 4 produtos
- Cartão Corporativo Itaú cadastrado como conta bancária
- 3 NFs de compra registradas (1 cancelada por teste)

### 🛡️ Infraestrutura
- **Backup versionado** — `Backup_ERP.bat` cria ZIPs datados no OneDrive, mantém últimas 10 versões
