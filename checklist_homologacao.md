# Checklist de Homologação: Fábrica de Alho (End-to-End) 🚀

Este é o guia de simulação extrema do ERP. O banco de dados já está povoado com saldos bancários de R$ 50.000, 4 fornecedores, 3 clientes e 4 produtos. Siga os passos na ordem para validar a matemática do sistema.

## Fase 1: Abastecimento (Compras e Pagamentos)
- [ ] **Módulo 2 (Compras):** Registre a compra de 1.000 Kg de **Alho In Natura (Sujo)** do fornecedor *Fazenda São José do Alho*. Coloque o valor de R$ 12,00 por Kg. Aprovar pedido.
- [ ] **Módulo 2 (Compras):** Compre 500 caixas de **Saco Plástico** do fornecedor *Plásticos SA*.
- [ ] **Módulo 5 (Estoque):** Verifique se entraram 1.000 Kg de matéria prima e 500 embalagens no galpão.
- [ ] **Módulo 9 (Financeiro > A Pagar):** Vá na aba "Contas a Pagar". Selecione os boletos da Fazenda e da Plásticos SA, marque a caixinha e confirme o pagamento saindo da *Conta Itaú Principal*.
- [ ] **Módulo 9 (Financeiro > Dashboard):** Confirme se o dinheiro reduziu da conta Itaú e se a régua gráfica registrou o passivo liquidado.

## Fase 2: Chão de Fábrica (Produção)
- [ ] **Módulo 4 (Produção):** Inicie um Lote Diário. Selecione que você quer produzir **Alho Descascado Premium**.
- [ ] Insira que você usou 1.000 Kg de matéria prima, mas obteve apenas 800 Kg de produto final (200 Kg foram perdas de casca). E consumiu 800 embalagens de Saco Plástico.
- [ ] **Módulo 5 (Estoque):** Verifique se a matéria prima zerou e se agora você tem 800 Kg de **Alho Descascado Premium** disponíveis para venda física.

## Fase 3: Venda Tripla (Testando Prazos Inteligentes)
- [ ] **Módulo 6 (Pedidos de Venda):** Faça uma venda de 200 Kg de Alho para a **Agrofruti**.
- [ ] Faça uma venda de 300 Kg para o **Supermercados Mundial**.
- [ ] Faça uma venda de 100 Kg para o **Sacolão do Silva**.

## Fase 4: Faturamento e Expedição (Logística)
- [ ] **Módulo 7 (Faturamento):** Selecione o pedido da **Agrofruti** e fature escolhendo a opção **DAV**.
- [ ] Selecione os pedidos do **Mundial** e do **Silva** e fature escolhendo a opção **Nota Fiscal (NF)**.
- [ ] **Módulo 8 (Logística):** Crie um Manifesto de Carga. Adicione os 3 pedidos faturados acima no mesmo caminhão. Mude o status para "Entregue" (simulando a volta do motorista com os canhotos).

## Fase 5: Tesouraria e Fechamento (O Grande Acerto)
- [ ] **Módulo 9 (Financeiro > Contas a Receber):** Desça a tela e abra a aba "Fechamento Semanal de Carteira (Fiado)". Selecione a **Agrofruti**.
- [ ] O sistema deve mostrar o DAV da Agrofruti gerado na Fase 4. Clique para gerar o Relatório Extrato A4 e confira se a formatação está perfeita.
- [ ] Vá no grid superior ("Acusar Recebimento em Lote"). Você verá que as contas caíram com os prazos exatos: Agrofruti (7 dias), Silva (28 dias) e Mundial (30 dias).
- [ ] Selecione o boleto da Agrofruti e liquide ele, informando que caiu na *Conta Itaú Principal*.

## Fase 6: Auditoria Contábil (DRE e BI)
- [ ] **Módulo 10 (DRE):** Abra a Demonstração de Resultados.
- [ ] Cheque a Linha 1: "Receita Líquida" (Ela computou a venda de todos os clientes?).
- [ ] Cheque a Linha de Custos Variáveis (O Alho Sujo comprado na Fase 1 foi debitado no Custo da Mercadoria Vendida?).
- [ ] Verifique no rodapé: O **EBITDA** está calculando o lucro limpo da operação sem o "buraco negro" de impostos?
