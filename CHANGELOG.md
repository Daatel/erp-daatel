# 📋 Histórico de Versões — ERP Fábrica de Alho

---

## v1.5 — 2026-05-16 (Sessão: Go-Live Nuvem, PostgreSQL e SaaS MVP)

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
