# Instruções de Continuidade: Kanban de Pedidos (V3) e Fluxo Horta do Príncipe

Olá, Antigravity! Este arquivo serve para orientá-lo sobre o estado atual do desenvolvimento e as tarefas pendentes para a implementação do Kanban de Pedidos integrado ao Supabase e Streamlit.

## 1. Contexto do Projeto

Estamos implementando o **Kanban de Pedidos (V3)** para gerenciar a programação de produção. Uma das principais novidades é o suporte ao **fluxo de repasse (pedidos casados)** de uma joint venture comercial com o distribuidor **Horta do Príncipe** para atender o **Atacadão**.

### Principais Documentos Disponíveis:
*   [MD_Kanban_de_pedidos.MD](file:///c:/Users/MARCIO/Gestao_Fabrica_Alho/MD_Kanban_de_pedidos.MD): Documento contendo a especificação de negócios e o guia de implementação técnica detalhado (inclui código SQL, código da Edge Function Deno, autenticação Streamlit e lógicas em JavaScript). 
    *   *Nota:* O arquivo está salvo com extensão `.MD`, mas a codificação interna é em formato RTF. Leia o arquivo com atenção para obter os códigos-fonte necessários.
*   [kanban_pedidos_producao_v3.html](file:///c:/Users/MARCIO/Gestao_Fabrica_Alho/kanban_pedidos_producao_v3.html): Protótipo estático do Kanban com design off-white e colunas verticais. Serve como base visual e de estilos inline para a implementação final.
*   `GRADE ATACADÃO HORTA EMPORIO 30 06 2026 (1).xlsx`: Planilha com a grade de pedidos do Atacadão usada como referência prática para os lotes.

---

## 2. Status Atual

Até o momento, foram realizadas as seguintes tarefas:
1.  Especificação do fluxo e definição da arquitetura técnica.
2.  Criação do mockup estático do Kanban (HTML/CSS).
3.  Salvamento do estado inicial do código no repositório Git local e envio das alterações para o repositório remoto (`https://github.com/Daatel/erp-daatel.git` no branch `main`).

Nenhum código de backend, migração de banco (Supabase) ou integração final no Streamlit foi executado ainda. **Toda a parte prática de implementação deve ser executada a partir de agora.**

---

## 3. Próximos Passos (Lista de Tarefas)

Siga o plano de desenvolvimento abaixo para completar a implementação:

- [ ] **Fase 1: Preparação do Banco de Dados (Supabase)**
  - [ ] Ler as especificações em `MD_Kanban_de_pedidos.MD` (Seção 1).
  - [ ] Executar o script SQL no SQL Editor do Supabase para criar os novos campos na tabela `pedidos` (`data_prevista`, `updated_at`, `flag_op_casada`, `grade_id`, `pedido_atacadao_numero`, `filial_atacadao`).
  - [ ] Criar a tabela `log_reprogramacao` e a tabela `feriados`.
  - [ ] Inserir os feriados nacionais/municipais de 2026.
  - [ ] Configurar os índices recomendados.

- [ ] **Fase 2: Configuração de Segurança (RLS)**
  - [ ] Habilitar Row Level Security (RLS) conforme a Seção 2 de `MD_Kanban_de_pedidos.MD`.
  - [ ] Configurar políticas para permitir apenas leitura (`SELECT`) pública/autenticada no front e restringir a gravação apenas para a conta de sistema (`service_role`).

- [ ] **Fase 3: Implementação da Edge Function**
  - [ ] Configurar as variáveis de ambiente e segredos no Supabase e no Streamlit (Seção 0).
  - [ ] Criar a Edge Function `mover-pedido` (`supabase/functions/mover-pedido/index.ts`) usando Deno/TypeScript para receber requisições assinadas e persistir mudanças (Seção 3).
  - [ ] Realizar o deploy da Edge Function com o comando `supabase functions deploy mover-pedido --no-verify-jwt`.

- [ ] **Fase 4: Integração do Streamlit e Front-end**
  - [ ] Implementar a geração de tokens JWT em Python (`auth_kanban.py`) usando a biblioteca `PyJWT` (Seção 4).
  - [ ] Integrar o código do Kanban no Streamlit através de `components.html`, substituindo os placeholders do Supabase e tokens gerados dinamicamente (Seção 7).
  - [ ] Adaptar o front-end JavaScript para carregar dados reais do Supabase em vez dos dados mockados do HTML (Seção 5 e 6).

- [ ] **Fase 5: Testes e Validação**
  - [ ] Seguir rigorosamente o checklist da Seção 9 em `MD_Kanban_de_pedidos.MD`.
  - [ ] Verificar o comportamento do Kanban sob concorrência (erros 409) e comportamento de arrastar itens sobre dias de feriados.

---
Seja minucioso e utilize as melhores práticas descritas no Brand Book/Diretrizes da DAATEL. Bom trabalho!
