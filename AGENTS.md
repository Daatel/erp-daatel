# Diretrizes de Desenvolvimento e Governança da DAATEL

## 1. Regra Anti-Banheira: Simplificação de Seleção
* **Não Duplicar Controles de Seleção:** É proibido criar "banheiras" — painéis inferiores ou secundários contendo selectboxes ou seletores de busca redundantes para realizar ações sobre itens que já estão listados e selecionados em uma tabela principal na mesma tela.
* **Ação Direta da Grid:** Se um item pode ser selecionado por meio de um checkbox ou marcação em uma grid/tabela, todas as ações operacionais correspondentes (ex: *Consolidar*, *Reverter Baixa*, *Excluir*, *Estornar*) devem atuar diretamente nos itens que receberam o check.
* **Botões Simétricos no Rodapé/Topo:** Os botões que executam as ações devem estar posicionados no rodapé ou no topo da grid correspondente, atuando em lote sobre as linhas marcadas pelo operador. Isso minimiza a carga cognitiva e o número de cliques.

---

## 2. Regra de Serviços Permanentes e Padrão Singleton (Gerenciamento de Processos)
* **Arquitetura de Execução Real:**
  ```text
  [Telegram] -> [Cloudflare Tunnel] -> [n8n :5678] -> [api_voice_bridge.py :8000] -> [PostgreSQL/Supabase]
  ```
* **Status dos Serviços (100% Singleton):**
  - `n8n`: Porta 5678 — **Máximo 1 instância**.
  - `Cloudflare Tunnel`: — **Máximo 1 instância**.
  - `api_voice_bridge.py`: Porta 8000 — **Máximo 1 instância**.

* **Regra Anti-Duplicação Estrita para Agentes de IA:**
  1. É estritamente **PROIBIDO** iniciar uma segunda instância de qualquer serviço sem verificar previamente se a porta já está em uso (`LISTENING`).
  2. Antes de subir a API REST `api_voice_bridge.py`, verificar via `netstat -ano | findstr ":8000"`. Se estiver em uso, utilizar a instância ativa.
  3. Utilizar sempre os scripts launchers com trava anti-duplicação:
     - `start_voice_bridge.cmd` (Porta 8000)
     - `start_n8n.cmd` (Porta 5678)

---

## 3. Regra de Incrementalidade Estrita (One-Layer-at-a-Time Rule)
* **Proibido Alterar Múltiplas Camadas em Paralelo:** Em diagnósticos ou refatorações de integrações complexas (Telegram -> Cloudflare -> n8n -> API -> NLU -> DB), o agente DEVE seguir obrigatoriamente a esteira de validação incremental de 1 camada por vez.
* **Ordem Sequencial de Validação:**
  - **FASE 1:** Conectividade Básica (`Telegram` -> `n8n` -> `Python Echo {"status": "received"}`)
  - **FASE 2:** Download de Mídia (`Python` -> `Telegram File API`)
  - **FASE 3:** Processamento NLU (`Python` -> `Gemini API`)
  - **FASE 4:** Extração Estruturada (`Pydantic VoiceCommandSchema`)
  - **FASE 5:** Negócio & Banco (`Fuzzy Matcher` -> `Rascunho Supabase`)
  - **FASE 6:** Confirmação & Efetivação (`DAV PDF` -> `Telegram Reply`)
