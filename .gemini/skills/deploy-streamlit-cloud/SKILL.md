---
name: deploy-streamlit-cloud
description: Regra de validação local do projeto. Nenhuma tarefa é dada por concluída até que esteja testada e validada no Streamlit Community Cloud (via branch main).
---

# ☁️ Diretriz Crítica: Validação em Nuvem (Streamlit Cloud)

Esta é uma **skill local e exclusiva do projeto Gestao_Fabrica_Alho**. Ela define que o critério de aceitação de qualquer entrega ou alteração de código é a sua efetiva disponibilização e funcionamento no ambiente de nuvem do cliente.

---

## 📋 Protocolo de Deploy e Validação em Nuvem

Para qualquer alteração de código, melhoria ou correção realizada neste repositório, o Agente de IA deve seguir estritamente os seguintes passos antes de considerar o bloco de trabalho como concluído:

### 1. Merge e Push para a Branch de Produção (`main`)
O ambiente de nuvem do cliente roda no **Streamlit Community Cloud** e está configurado para refletir a branch **`main`**. Portanto:
* Assim que as alterações locais forem testadas e consolidadas na branch de trabalho (ex: `feature-resilience`), realize o checkout para a branch `main`.
* Faça o merge das alterações (`git merge <branch-de-trabalho>`).
* Faça o push das alterações para o repositório remoto (`git push origin main`).
* Retorne para a branch de trabalho.

### 2. Acompanhamento do Tempo de Build
* O Streamlit Community Cloud leva em média de **1 a 2 minutos** para compilar e implantar a nova versão do código após receber o push.
* Informe ao usuário que o push foi realizado com sucesso para a branch de produção e que o deploy está sendo atualizado na nuvem.

### 3. Validação e Confirmação de Produção
* **NUNCA** diga que uma tarefa está pronta, finalizada ou entregue baseando-se apenas no funcionamento do ambiente de desenvolvimento local.
* A tarefa só é considerada **concluída** após o Agente ou o Usuário acessar a URL de produção na nuvem e constatar que a alteração está ativa e funcionando perfeitamente lá.

---

## ⚡ Regra de Ouro do Projeto
O sucesso do cliente é medido pelo que está no ar. Se o código não foi para o ar (Streamlit Cloud), a tarefa **não** está pronta.
