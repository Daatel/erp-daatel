# Especificação Técnica: Módulo de Faturamento (Empório do Alho ERP)

## 1. Visão Geral
Este documento detalha o funcionamento e a integração do módulo de faturamento para o sistema de gestão da manufatura de alho e temperos. O objetivo é transformar pedidos de venda aprovados em registros de faturamento, realizando a baixa de estoque em tempo real e gerando arquivos para exportação fiscal.

## 2. Fluxo de Processo (Workflow)

1.  **Ingestão de Dados:** O módulo consome pedidos do módulo de **Vendas** com status `APROVADO`.
2.  **Gestão de Fila:** O usuário visualiza os pedidos em uma interface de grade (Data Grid) e define a ordem de prioridade.
3.  **Processamento de Faturamento:**
    * O sistema percorre a fila conforme a prioridade definida.
    * Para cada item do pedido, consulta o módulo de **Estoque**.
    * Se houver saldo: Realiza a baixa do estoque e marca o pedido como `FATURADO`.
    * Se não houver saldo: O pedido permanece na fila como `PENDENTE - FALTA DE ESTOQUE` e o sistema prossegue para o próximo pedido da fila.
4.  **Saída de Dados:**
    * Geração automática de lançamentos no módulo **Financeiro** (Contas a Receber).
    * Geração de arquivo de exportação (TXT/XML) no padrão SEFAZ para importação em emissor de terceiros.

## 3. Integração entre Módulos

| Origem/Destino | Módulo | Ação | Dados Necessários |
| :--- | :--- | :--- | :--- |
| **Origem** | Vendas | Buscar Pedidos | ID_Pedido, Cliente (CNPJ/Dados), Itens, Quantidade, Valor Unitário, Condição de Pagamento. |
| **Interação** | Estoque | Validar e Baixar | SKU/ID_Produto, Quantidade a abater. |
| **Destino** | Financeiro | Criar Lançamento | Valor Total, Data de Vencimento (baseado na condição de venda), ID_Faturamento. |
| **Saída** | Exportador Fiscal | Gerar Arquivo | Dados completos do cliente, NCM, CFOP, Pesos (Bruto/Líquido), Valor Total. |

## 4. Lógica de Priorização (Engine)

O sistema deve permitir a reordenação manual dos pedidos.
* **Input:** Lista de pedidos `[P1, P2, P3, ... Pn]`.
* **Ação:** O usuário atribui um índice de prioridade ou arrasta as linhas na UI.
* **Execução em Lote:** Ao clicar em "Processar Faturamento", o sistema executa um loop `FOR EACH` respeitando a ordem do índice.
* **Regra de Inventário:** A baixa de estoque é **atômica** por pedido. Se um pedido de 100kg de alho processar, ele retira 100kg do estoque global antes que o pedido de prioridade inferior seja avaliado.

## 5. Requisitos de Interface (UI/UX)

* **Componente:** Data Grid Interativa (Tabela).
* **Funcionalidades:**
    * Filtro por Rota/Região de entrega.
    * Sinalizador visual (Farol) de disponibilidade de estoque (Verde: Tudo disponível | Amarelo: Parcial | Vermelho: Sem estoque).
    * Botão "Gerar Arquivo SEFAZ" para os pedidos faturados.

## 6. Especificação do Arquivo de Saída (Exportador)

O sistema deve compilar os dados do faturamento no layout de importação do Emissor Gratuito (Sebrae) ou padrão XML NF-e.
* **Campos Fixos sugeridos para o Empório do Alho:**
    * NCM Alho Descascado: `0703.20.90`
    * CFOP Padrão (Venda Industrialização): `5.101` (Interna) ou `6.101` (Interestadual).
    * Cálculo automático de Peso Bruto (Peso Líquido + margem de embalagem).

## 7. Estrutura de Banco de Dados (Sugestão)

### Tabela: `faturamento_movimentacao`
* `id`: UUID
* `pedido_origem_id`: FK (Vendas)
* `status`: (Pendente, Processado, Erro_Estoque)
* `prioridade_index`: Integer
* `data_processamento`: Timestamp
* `arquivo_gerado`: Boolean

### Tabela: `financeiro_receber` (Gerada via Trigger do Faturamento)
* `faturamento_id`: FK
* `valor`: Decimal
* `vencimento`: Date
* `status_pagamento`: (Aberto, Pago)
