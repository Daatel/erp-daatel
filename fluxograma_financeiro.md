# Fluxograma: Módulo Financeiro & Tesouraria

```mermaid
flowchart TD
    classDef painel fill:#0284c7,stroke:#fff,stroke-width:2px,color:#fff
    classDef manual fill:#01743d,stroke:#fff,stroke-width:2px,color:#fff
    classDef robo fill:#7e22ce,stroke:#fff,stroke-width:2px,color:#fff
    classDef fluxo fill:#059669,stroke:#fff,stroke-width:2px,color:#fff

    A([Títulos Pendentes]) --> B(Contas a Pagar)
    A --> C(Contas a Receber)

    B --> D[Baixa em Lote: Data Grid Checkboxes]
    C --> D

    D -->|Edição de Juros se Necessário| E(Seleciona Conta/Banco e Data)
    E --> F{Confirmar Lote}

    F -->|Atualiza BD| G[Injeta Registros no Fluxo de Caixa Real]
    G --> H[Alimenta Dashboard DRE Executivo]

    I([Extrato Bancário .CSV]) --> J[Robô de Conciliação]
    J --> K{Cruzar Valores Absolutos}
    K -->|Match Encontrado| L[Marcar como 'CONCILIADO' (Auditado)]

    class A,H painel
    class B,C,D,E manual
    class I,J,K,L robo
    class F,G fluxo
```
