# 🧄 ERP Fábrica de Alho - Relatório de Pass Over (Handoff) 🚀

Este documento contém o estado consolidado do projeto ERP Fábrica de Alho para que um novo agente de IA (como Claude 3.5 Sonnet ou Gemini 1.5 Pro) possa assumir o desenvolvimento e homologação instantaneamente com contexto perfeito.

---

## 📌 1. Visão Geral do Projeto
O ERP da Fábrica de Alho foi construído em **Python** utilizando a biblioteca **Streamlit** e integrado a um banco de dados **PostgreSQL hospedado no Supabase** (em nuvem).

* **Objetivo Atual:** Finalizar a homologação do sistema simulando o fluxo de ponta a ponta (Compras, Produção, Vendas, Faturamento, Logística, Financeiro e DRE).
* **URL de Produção na Nuvem:** [https://daatel-erp.streamlit.app/](https://daatel-erp.streamlit.app/)
* **Diretório Oficial de Trabalho:** `C:\Users\MARCIO\Gestao_Fabrica_Alho`

---

## 📂 2. Arquivos Complementares do Sistema de Agentes (Essenciais para Leitura)
Os metadados e o progresso profundo das sessões anteriores estão salvos na pasta interna do sistema em **`C:\Users\MARCIO\.gemini\antigravity\brain\b9c001df-1614-4b5b-b6f8-b36d4e9d413f\`**. 

O novo agente de IA deve ler os seguintes 3 arquivos contidos lá para obter o histórico técnico completo:

1. 📄 **`walkthrough.md`**  
   * **Caminho:** `C:\Users\MARCIO\.gemini\antigravity\brain\b9c001df-1614-4b5b-b6f8-b36d4e9d413f\walkthrough.md`  
   * **Conteúdo:** Histórico detalhado de todas as alterações feitas, sessões de deploy e mudanças de arquitetura.
2. 📄 **`implementation_plan.md`**  
   * **Caminho:** `C:\Users\MARCIO\.gemini\antigravity\brain\b9c001df-1614-4b5b-b6f8-b36d4e9d413f\implementation_plan.md`  
   * **Conteúdo:** O plano de arquitetura original e o mapeamento dos fluxos do ERP.
3. 📄 **`task.md`**  
   * **Caminho:** `C:\Users\MARCIO\.gemini\antigravity\brain\b9c001df-1614-4b5b-b6f8-b36d4e9d413f\task.md`  
   * **Conteúdo:** Checklist técnico de todas as tarefas concluídas.

---

## 💡 3. Histórico de Problemas Críticos Resolvidos (ATENÇÃO: Evitar Regressão!)

Para evitar que a nova IA sobrescreva soluções de problemas complexos do passado, aqui está o detalhamento dos erros que foram corrigidos:

### ⚠️ A. Confusão de Repositórios Git Duplicados (Resolvido)
* **O Problema:** Havia dois diretórios locais parecidos: a pasta física `C:\Users\MARCIO\Gestao_Fabrica_Alho` (onde o desenvolvimento real e o Git estavam) e a pasta do OneDrive `C:\Users\MARCIO\OneDrive\Gestao_Fabrica_Alho` (uma cópia desatualizada, sem pasta `.git`). Isso causava divergência de arquivos e erros de sincronização. Além disso, a referência local `.git/refs/remotes/origin/main` estava corrompida (zerada/vazia), travando comandos como `git fetch` e `git status`.
* **A Solução:**
  1. A pasta desatualizada do OneDrive foi renomeada para `C:\Users\MARCIO\OneDrive\Gestao_Fabrica_Alho_DESATIVADO_ANTIGO` (isolando-a totalmente e com segurança).
  2. O arquivo corrompido de referência do Git foi excluído e recriado com `git fetch origin`. Agora o Git está **100% íntegro e sincronizado** com o GitHub.
  3. A única pasta oficial de desenvolvimento é: `C:\Users\MARCIO\Gestao_Fabrica_Alho`.

### ⚠️ B. Erros Anteriores com Logins e Conexão na Nuvem (Resolvido)
* **O Problema:** Inicialmente, após o deploy no Streamlit Community Cloud, ocorriam falhas graves de login e quedas de conexão. O motivo era que a aplicação Streamlit roda em ambiente multi-thread e as conexões simples do PostgreSQL (`psycopg2.connect`) não eram thread-safe, sofrendo concorrência e fechando inesperadamente.
* **A Solução:**
  1. Refatoramos `database.py` para usar um pool de conexões thread-safe: `psycopg2.pool.ThreadedConnectionPool(1, 10, st.secrets["DATABASE_URL"])`.
  2. Criamos funções estritas de `get_connection()` e `release_connection(conn)` que garantem que cada transação pegue uma conexão limpa do pool e a devolva imediatamente após o uso.
  3. **ATENÇÃO:** O novo agente de IA **deve preservar essa estrutura de ThreadedConnectionPool** em `database.py` para evitar que os erros de login e queda de banco retornem no ambiente Streamlit Cloud!

---

## 🛠️ 4. Estado Técnico Atual
1. **Diferença de Arquivos:** Todos os desenvolvimentos novos (Dashboards, Comodatos, DRE, etc.) estão consolidados unicamente em `C:\Users\MARCIO\Gestao_Fabrica_Alho`. Nenhum arquivo novo foi perdido na pasta do OneDrive.
2. **Repositório GitHub:** `https://github.com/Daatel/erp-daatel.git` na branch `main`.

---

## 📊 5. Credenciais e Perfis de Acesso para Homologação

Para realizar testes na interface do Streamlit:

* **Senha Mestra (Bypass Rápido):** `daatel2026`
* **Usuários do Banco (para simular perfis e cargos):**
  * **Administrador:** `admin@alho.com` | Senha: `admin123`
  * **Financeiro:** `fin@alho.com` | Senha: `fin123`
  * **Vendas:** `vendas@alho.com` | Senha: `vend123`
  * **Produção:** `fabrica@alho.com` | Senha: `fab123`
  * **Compras:** `compras@alho.com` | Senha: `comp123`

---

## 📋 6. Roteiro e Checklist de Homologação (Fases 1 a 6)

O arquivo `checklist_homologacao.md` na raiz do projeto detalha a simulação de ponta a ponta:

1. **Fase 1 (Abastecimento):** Comprar Alho In Natura (1.000 kg a R$ 12/kg) e 500 sacos de embalagem. Liquidar os boletos no Financeiro (Itaú).
2. **Fase 2 (Produção):** Iniciar lote de Alho Descascado Premium (usando 1.000 kg sujo, obtendo 800 kg limpo e gerando perda de 200 kg de casca).
3. **Fase 3 (Venda):** Registrar 3 pedidos de venda para Agrofruti (200 kg), Mundial (300 kg) e Silva (100 kg) com comissões correspondentes.
4. **Fase 4 (Faturamento/Logística):** Faturar os pedidos em DAV ou NF, criar Manifesto de Carga e simular entrega.
5. **Fase 5 (Financeiro/Tesouraria):** Realizar recebimento do fiado (Agrofruti) e liquidações de carteira.
6. **Fase 6 (Auditoria Contábil):** Validar se o EBITDA e a DRE estão batendo perfeitamente na tela.

---

## 🚀 7. Próximos Passos Recomendados para o Novo Agente
1. **Entrar no Link da Nuvem:** Acessar [https://daatel-erp.streamlit.app/](https://daatel-erp.streamlit.app/) e garantir que o banner de cache do Streamlit seja limpo (pressionando **Ctrl + F5** se necessário).
2. **Iniciar Simulação no Browser:** Efetuar o login como `admin@alho.com` e seguir o checklist passo a passo.
3. **Se necessário, testar scripts automáticos de homologação localmente:**
   * Rodar `python homologacao_drill.py` (Fases 1 e 2 automáticas).
   * Rodar `python homologacao_fase3_5.py` (Fases 3, 4 e 5 automáticas).
