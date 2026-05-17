# Fluxograma: Módulo de Faturamento & Expedição

```mermaid
flowchart TD
    classDef fila fill:#ca8a04,stroke:#fff,stroke-width:2px,color:#fff
    classDef user fill:#01743d,stroke:#fff,stroke-width:2px,color:#fff
    classDef system fill:#292d77,stroke:#fff,stroke-width:2px,color:#fff
    classDef docs fill:#4b5563,stroke:#fff,stroke-width:2px,color:#fff

    A([Fila de Pedidos APROVADOS]) --> B[Data Grid (Seleção em Lote)]
    
    B --> C{Farol de Estoque Físico}
    C -->|🟢 OK| D(Marcar Checkbox)
    C -->|🔴 Sem Saldo| D(Marcar Checkbox - Autorizado)

    D --> E{Processar Lote}

    E -->|Ação 1| F[Muda Status Venda para 'FATURADO']
    E -->|Ação 2| G[Baixa de Estoque de Produto Acabado]
    E -->|Ação 3| H[Gera Título no Contas a Receber]

    I[Mês Fechado / Contábil] --> J[Gerador Fiscal SEFAZ]
    J --> K[Carimba NCM 0703.20.90]
    J --> L{UF do Cliente = UF Fábrica?}
    L -->|Sim| M[Aplica CFOP 5101]
    L -->|Não| N[Aplica CFOP 6101]
    
    M --> O[Gera Arquivo .CSV / .TXT]
    N --> O

    class A fila
    class B,D,I user
    class C,E,F,G,H,J,K,L,M,N system
    class O docs
```
