---
name: atualizar-changelog
description: Enforces mandatory updating of CHANGELOG.md at the end of every development session or feature implementation in the DAATEL ERP project.
---

# Diretriz de Atualização Obrigatória do CHANGELOG.md — ERP DAATEL

> 💡 **Escopo Estrito:** Esta skill aplica-se **exclusivamente** às sessões de desenvolvimento deste projeto (`Gestao_Fabrica_Alho`), onde o arquivo `CHANGELOG.md` está presente na raiz.

Para garantir que o histórico do sistema permaneça 100% auditável, sincronizado com os commits e transparente para o cliente e equipe, é **OBRIGATÓRIO** atualizar o arquivo `CHANGELOG.md` na raiz do projeto ao final de cada sessão de desenvolvimento ou alteração relevante de código.

---

## 📌 Regras de Execução Obrigatórias para o Agente IA

1. **Verificação de Encerramento de Sessão:**
   - Antes de considerar qualquer tarefa finalizada ou realizar um `git commit` / `git push`, o agente DEVE verificar se o arquivo `CHANGELOG.md` reflete todas as alterações realizadas na sessão atual.

2. **Formato Padrão de Entrada:**
   A nova entrada DEVE ser inserida **no topo do arquivo `CHANGELOG.md`** (logo abaixo do título principal), seguindo a estrutura semântica:

   ```markdown
   ## vX.Y — YYYY-MM-DD (Sessão: [Resumo Sucinto da Sessão / Feature Principal])

   ### 🚀 [Nome do Módulo / Recurso] (`arquivos_afetados.py`)
   - **Recurso / Correção:** Detalhamento técnico e funcional das alterações.
   - **Regras de Negócio / UX:** Decisões operacionais de fluxo, segurança, alçadas e interface.

   ### 🗄️ Banco de Dados & Migrations (`database.py`)
   - **DDL / Schemas:** Tabelas, colunas, índices ou seeds adicionadas na sessão.
   ```

3. **Checklist de Validação:**
   - [ ] Número da versão incrementado (`vX.Y`).
   - [ ] Data no formato ISO `YYYY-MM-DD`.
   - [ ] Todos os módulos e arquivos criados/modificados mapeados.
   - [ ] `CHANGELOG.md` incluído no `git add` e commitado junto com as alterações da sessão.
