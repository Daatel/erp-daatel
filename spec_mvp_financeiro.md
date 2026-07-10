# Especificação — MVP Módulo Financeiro (Cockpit Diário)

## Contexto e Princípio de Design

Usuário-alvo: gestor de fábrica pequena, sem cultura de dados, sem hábito de análise financeira formal.

Princípio norteador do MVP: a tela deve responder, em poucos segundos de leitura, à pergunta **"a situação de caixa hoje está favorável ou desfavorável?"**. Toda decisão de escopo abaixo prioriza clareza e formação de hábito de uso diário em detrimento de profundidade analítica. Profundidade entra no backlog v2, após o hábito estar consolidado.

Diretrizes de linguagem visual (aplicam-se a todas as telas):
- Sem emojis. Sem termos coloquiais ou exclamações informais.
- Hierarquia visual construída por tamanho de fonte, peso (negrito) e cor de indicador — não por ícones decorativos.
- Cor como portador de significado (favorável / atenção / desfavorável), aplicada em barra lateral, fundo sutil de card ou indicador pontual — nunca como o único meio de comunicar o dado (acompanhar sempre de texto/valor).
- Tom sóbrio e institucional, compatível com uso por proprietário, controller ou contador externo.

---

## 1. Banco de Dados (Migração)

### [MODIFY] `contas_bancarias`
- Adicionar coluna `limite_credito` (NUMERIC/DECIMAL, default `0.0`) em SQLite (`erp_fabrica.db`) e PostgreSQL (produção).
- Migração deve ser idempotente e versionada (ex.: `migrations/002_add_limite_credito.sql`), com verificação de existência da coluna antes de aplicar (`PRAGMA table_info` no SQLite; `IF NOT EXISTS` no PostgreSQL).
- Definir estratégia de rollback explícita.
- Após aplicar a migração, listar contas com `limite_credito = 0.0` e sinalizar para preenchimento manual (evitar leitura incorreta de "sem limite" quando na verdade é "não configurado").

---

## 2. Cadastros Básicos

### [MODIFY] `pages/1_Cadastros.py`
- Incluir campo **Limite de Crédito (Cheque Especial)** no formulário de criação e edição de contas bancárias.
- Validação: valor não pode ser negativo.
- Acesso de edição restrito a perfil financeiro/controller, se o sistema já possuir controle de perfis.
- Registrar em log/auditoria: usuário, data/hora, valor anterior e novo valor, sempre que o limite de crédito for alterado.

---

## 3. Painel Financeiro — Escopo MVP (v1)

### [MODIFY] `pages/9_Financeiro.py`

A tela é única, sem alternância manual entre abas. O conteúdo muda automaticamente conforme o horário do sistema:
- Período da manhã → modo Projeção.
- Período da tarde/fechamento → modo Realizado.
- Definir horário de corte explícito (ex.: 13h) e fuso horário de referência (servidor ou usuário) antes da implementação.

### 3.1 Cabeçalho — Saldo Disponível

- Exibir um único valor consolidado: **Saldo Disponível Hoje** (saldo atual em conta + limite de crédito das contas correspondentes).
- Indicador de cor (favorável / atenção / desfavorável) associado a esse valor, com limiares configuráveis.
- Nota textual discreta indicando que o valor inclui limite de crédito.

### 3.2 Saldos por Conta

- Exibir como cards individuais (não tabela densa), um por conta bancária:
  - Nome da conta.
  - Saldo atual.
  - Indicador de cor.
- Limite de crédito não aparece como número solto nesta visão; está incorporado apenas no cálculo do saldo disponível do cabeçalho (3.1). Detalhe do limite por conta disponível ao expandir o card.

### 3.3 Compromissos do Dia (modo Projeção)

- Duas listagens: valores a receber hoje e valores a pagar hoje.
- Cada item exibe: descrição, valor, e **categoria do Plano de Contas** (nome da categoria, ex.: "Energia/Água" — sem exibir o código numérico na visão padrão; código disponível ao expandir o item).
- Lançamento sem categoria associada deve ser sinalizado visualmente como pendente de classificação, com ação direta para classificá-lo. Este mecanismo tem propósito didático: reforçar ao usuário o hábito de classificar despesas e receitas corretamente.
- Soma de entradas e soma de saídas do dia, exibidas em destaque acima de cada listagem.

### 3.4 Atrasados (modo Projeção)

- Exibir um valor único consolidado de total em atraso (a receber e a pagar, separadamente), com indicador de atenção.
- Detalhamento por faixa de aging (0–30 / 31–60 / 60+ dias) disponível ao expandir — não exibido por padrão na tela inicial.
- Definir critério explícito de corte para "em atraso" (quantos dias após o vencimento o item passa a ser contabilizado).

### 3.5 Tendência (modo Projeção)

- Indicador simples de tendência (variação em relação ao dia anterior: alta, estável ou queda), sem gráfico de série temporal no MVP.

### 3.6 Fechamento do Dia (modo Realizado)

- Comparação direta: saldo de fechamento de ontem versus saldo de fechamento de hoje, com variação em valor absoluto.
- Listagem de recebimentos e pagamentos efetivamente realizados no dia, cada item com descrição, valor e categoria do Plano de Contas (mesmo padrão do item 3.3).
- Confirmação de conciliação: controle simples (sim/não) por conta, indicando se o saldo foi conferido contra o extrato bancário. Sinalizador detalhado de conciliação (percentual, exceções automáticas) fica para o backlog v2.

### 3.7 Geração de PDF

- Botão para gerar PDF de uma página, contendo o resumo visual do fechamento do dia (saldo, variação, recebimentos e pagamentos com categoria).
- Especificar biblioteca de geração antes da implementação (ex.: ReportLab, WeasyPrint ou equivalente já em uso no projeto) e critério de aceite de formatação (margens, comportamento em caso de lista longa).

### 3.8 Especificação Visual (UI) — Mapeamento para Streamlit

Diretrizes gerais de estilo (válidas para as duas visões):
- Sem emojis em nenhum elemento (títulos, botões, mensagens, PDF).
- Hierarquia por tamanho/peso de fonte e cor de indicador lateral (barra de 3px), não por ícone decorativo.
- Paleta de indicador: verde (favorável), amarelo/âmbar (atenção), vermelho (desfavorável) — aplicada como borda lateral de card ou fundo sutil, sempre acompanhada de texto/valor.
- Injetar um bloco único de CSS customizado no topo da página (`st.markdown("<style>...</style>", unsafe_allow_html=True)`) centralizando essas regras, evitar CSS disperso pelo arquivo.

**Cabeçalho e alternância de visão**
- Título da página + data corrente alinhados à esquerda.
- Controle segmentado de duas opções ("Projeção do dia" / "Fechamento do dia") alinhado à direita, usando `st.segmented_control` (Streamlit ≥ 1.35) ou, se indisponível na versão instalada, `st.radio` com `horizontal=True` estilizado para parecer segmented control.
- A alternância é reativa (rerender imediato do bloco de conteúdo abaixo), sem reload de página.

**Cabeçalho — Saldo Disponível (3.1)**
- Bloco único em destaque, não em `st.metric` padrão (que não permite borda lateral colorida nem nota textual secundária) — usar `st.container(border=True)` com CSS injetado para a borda lateral, contendo: rótulo pequeno, valor grande, nota discreta, selo textual de situação (ex.: "Situação favorável") alinhado à direita do bloco.

**Saldos por conta (3.2)**
- `st.columns(n)` com um `st.container(border=True)` por conta dentro de cada coluna, borda lateral colorida via CSS por classe/atributo condicional em Python (cor calculada antes da renderização).
- Detalhe do limite de crédito por conta: usar `st.expander` dentro do próprio container do card, rotulado de forma neutra (ex.: "Detalhes da conta").

**Alerta de atrasados (3.4)**
- Usar `st.warning()` nativo para o valor consolidado, mantendo o tom padrão do Streamlit (sem emoji customizado sobrescrevendo o ícone padrão do componente — se o ícone padrão do `st.warning` for indesejado, usar `icon=None` ou parâmetro equivalente da versão instalada).
- Detalhamento por faixa de aging dentro de `st.expander` acionado a partir do próprio aviso.

**Compromissos do dia / Movimentações realizadas (3.3 e 3.6)**
- Não usar `st.dataframe` ou `st.table` para esta listagem (resultaria em tabela densa, contrária ao princípio de simplicidade do MVP).
- Renderizar item a item: um bloco por lançamento com descrição e categoria (subtexto em `var(--text-muted)` equivalente, ou `st.caption`) à esquerda e valor alinhado à direita — usar `st.columns([3,1])` por linha dentro de um loop, com `st.divider()` fino entre itens ou borda inferior via CSS.
- Lançamento sem categoria: aplicar destaque de cor de atenção no texto da categoria (ex.: `st.caption` com HTML inline colorido) e tornar o item clicável (`st.button` discreto ou link) para abrir o formulário de classificação.

**Tendência (3.5)**
- Elemento textual simples ao lado do saldo ou do cabeçalho, sem gráfico — ex.: `st.caption` com seta (caractere tipográfico ▲/▼, não emoji) e palavra (alta/estável/queda).

**Fechamento do dia — comparação e conciliação (3.6)**
- Comparação ontem/hoje: dois `st.container(border=True)` lado a lado via `st.columns(2)`, mesmo padrão visual dos cards de saldo.
- Tabela de conciliação por conta: este é o único caso do painel em que uma tabela é apropriada (dado tabular real, poucas linhas, ação binária por linha) — usar `st.data_editor` com coluna de checkbox editável para o campo de conciliação, evitando implementar `st.checkbox` solto por linha fora de um componente tabular.

**Geração de PDF (3.7)**
- `st.download_button` com rótulo textual direto (ex.: "Baixar fechamento em PDF"), sem emoji no rótulo.
- Arquivo gerado em memória (`BytesIO`) antes do clique não é necessário — Streamlit permite gerar sob demanda no callback do botão, mas para PDF de geração custosa considerar gerar antecipadamente e cachear com `st.cache_data` por período do dia.

---

## 4. Backlog v2 (Pós-MVP)

Itens deliberadamente adiados até que o uso diário do MVP esteja consolidado:

| Item | Motivo do adiamento |
|---|---|
| Aging detalhado por faixa (0–30/31–60/60+) como visão padrão | Exige adoção prévia do hábito de checagem diária |
| Gráfico de fluxo de caixa (15–30 dias) | Leitura de gráfico de série temporal não é intuitiva para o público-alvo inicial; indicador de tendência simples cobre a necessidade imediata |
| Simulação de impacto de atrasados na projeção futura | Funcionalidade avançada, depende de regra de negócio ainda a definir (distribuição do valor em atraso ao longo dos próximos dias) |
| Sinalizador de conciliação detalhado (percentual, exceções automáticas via integração bancária) | Depende de integração bancária (OFX/API) ainda não escopada |
| Comparação Projetado x Realizado (acurácia de forecast) | Relevante, mas requer histórico acumulado de pelo menos algumas semanas de uso |
| Drill-down completo em todos os valores | Adicionar sob demanda, conforme uso real indicar necessidade |
| Exportação para Excel e distribuição automática por e-mail | Conveniência operacional, não bloqueia a decisão diária |

---

## 5. Plano de Verificação

### Testes automatizados
- Compilação sintática de todos os arquivos modificados:
  ```
  python -m py_compile database.py pages/1_Cadastros.py pages/9_Financeiro.py
  ```
- Testes de cálculo (obrigatórios, não cobertos por compilação):
  - Saldo Disponível = Saldo Atual + Limite de Crédito, para conjunto de dados conhecido.
  - Soma de compromissos do dia (entradas e saídas) confere com fixture de teste.
  - Classificação correta de item em atraso considerando o critério de corte definido (casos de borda: exatamente no dia do vencimento, exatamente 30/31/60/61 dias).
  - Migração aplicada em cópia de banco de teste não corrompe dados existentes e preenche `limite_credito` com o default correto.
- Testes de paridade SQLite x PostgreSQL para as queries novas do painel.

### Verificação manual
1. Cadastrar e editar limite de crédito em conta bancária existente; confirmar gravação correta em ambos os bancos de dados.
2. Verificar que a tela do Financeiro alterna corretamente entre modo Projeção e modo Realizado conforme o horário definido.
3. Confirmar que lançamentos sem categoria no Plano de Contas aparecem sinalizados e podem ser classificados diretamente pela tela.
4. Gerar o PDF de fechamento e validar formatação em página A4.
5. Confirmar que o indicador de cor do saldo disponível responde corretamente aos limiares configurados (favorável / atenção / desfavorável).
