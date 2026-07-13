# Diretrizes de Design de Interface e Usabilidade da DAATEL

Para garantir que a experiência do usuário seja extremamente fluida, limpa e profissional, todas as interações com o sistema devem seguir as seguintes regras de design de interface (UI/UX).

## 1. Regra Anti-Banheira: Simplificação de Seleção
* **Não Duplicar Controles de Seleção:** É proibido criar "banheiras" — painéis inferiores ou secundários contendo selectboxes ou seletores de busca redundantes para realizar ações sobre itens que já estão listados e selecionados em uma tabela principal na mesma tela.
* **Ação Direta da Grid:** Se um item pode ser selecionado por meio de um checkbox ou marcação em uma grid/tabela, todas as ações operacionais correspondentes (ex: *Consolidar*, *Reverter Baixa*, *Excluir*, *Estornar*) devem atuar diretamente nos itens que receberam o check.
* **Botões Simétricos no Rodapé/Topo:** Os botões que executam as ações devem estar posicionados no rodapé ou no topo da grid correspondente, atuando em lote sobre as linhas marcadas pelo operador. Isso minimiza a carga cognitiva e o número de cliques.
