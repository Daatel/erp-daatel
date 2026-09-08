# Importação de Folha Fotografada via Gemini Vision
## Especificação Técnica — ERP Daatel / Empório do Alho

---

## 1. Contexto

Este módulo complementa a Mesa de Seleção permitindo que a operadora
fotografe a folha diária preenchida à mão e importe os dados diretamente
para o sistema, sem digitação manual.

O Antigravity já usa Gemini. Este módulo usa a mesma API — Google Gemini
Vision (gemini-1.5-flash) — para ler a imagem e extrair os dados em JSON.

---

## 2. Fluxo Completo

```
1. Operadora imprime a folha do dia (PDF gerado pelo sistema)
2. Selecionadoras preenchem os pesos à mão durante o turno
3. Ao final do dia: operadora fotografa a folha
4. Abre o ERP → Mesa de Seleção → "Importar folha fotografada"
5. Faz upload ou tira foto diretamente pelo celular (st.camera_input)
6. Sistema envia imagem para Gemini Vision API
7. Gemini retorna JSON estruturado com pesagens e descarte
8. Sistema exibe tabela de confirmação — operadora revisa e corrige
9. Operadora confirma → dados salvos no banco (mesmo fluxo do lançamento manual)
```

---

## 3. Dependências

```bash
pip install google-generativeai pillow
```

Variável de ambiente necessária (já deve existir no Antigravity):
```
GEMINI_API_KEY=...
```

Se não existir, adicionar ao `.env` ou `st.secrets`:
```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "sua-chave-aqui"
```

---

## 4. Prompt enviado ao Gemini

```
Você está lendo uma folha de pesagem de selecionadoras de uma fábrica de alho.

A folha tem duas seções:

SEÇÃO 1 — PESAGEM INDIVIDUAL
Tabela com colunas: #, Nome, Meta (kg), Pesagem 1, Pesagem 2, Total (kg)
Extraia apenas o Nome e o Total (kg) de cada linha preenchida.
Ignore linhas onde o Total estiver em branco ou ilegível.

SEÇÃO 2 — DESCARTE X 2A LINHA
Tabela com linhas: Alho Nobre, 2ª Linha, Descarte
Extraia o Peso (kg) de cada linha.

Retorne APENAS um JSON válido, sem texto antes ou depois, sem markdown,
no seguinte formato exato:

{
  "pesagens": [
    { "nome": "Maria Souza", "total_kg": 88.5 },
    { "nome": "Ana Lima",    "total_kg": 95.0 }
  ],
  "nobre_kg":         420.0,
  "segunda_linha_kg":  85.0,
  "descarte_kg":       32.0,
  "confianca":         "alta",
  "avisos":           []
}

Regras:
- total_kg, nobre_kg, segunda_linha_kg, descarte_kg: número decimal ou null se ilegível
- confianca: "alta" | "media" | "baixa" conforme qualidade da imagem/caligrafia
- avisos: lista de strings descrevendo campos ilegíveis ou suspeitos
- Nunca invente valores. Se ilegível, retorne null.
```

---

## 5. Estrutura do Componente

```
components/selecao/
└── ocr_folha.py        ← novo arquivo
```

Integração na mesa.py:
```python
# Adicionar botão na Mesa de Seleção (passo 2)
from .ocr_folha import render_importar_folha
```

---

## 6. Checklist para o Antigravity

- [ ] Verificar se `GEMINI_API_KEY` já está configurada no projeto
- [ ] Verificar se `google-generativeai` já está instalado no requirements.txt
- [ ] Verificar se `pillow` já está instalado
- [ ] Confirmar modelo disponível: `gemini-1.5-flash` (mais rápido e barato)
        alternativa: `gemini-1.5-pro` (mais preciso para caligrafia ruim)
- [ ] Confirmar que `st.camera_input` está habilitado (requer HTTPS em produção)
- [ ] Não há alteração de banco de dados neste módulo —
        os dados confirmados seguem o mesmo fluxo de save da mesa.py

---

## 7. Tratamento de Erros

| Situação                        | Comportamento                                      |
|---------------------------------|----------------------------------------------------|
| Foto muito escura ou borrada    | Gemini retorna confianca "baixa" + avisos          |
| Campo ilegível                  | Retorna null — campo fica em branco na tela        |
| Nome não bate com presentes     | Sistema alerta mas não bloqueia — operadora decide |
| JSON inválido retornado          | Exibe erro + opção de tentar novamente             |
| API fora do ar                  | Exibe erro + fallback para lançamento manual       |
| Foto de documento errado        | Gemini retorna pesagens vazio — sistema alerta     |

---

## 8. Custo estimado

Gemini 1.5 Flash:
- Input: ~$0.075 por 1M tokens (imagem ~300 tokens)
- Custo por foto: < $0.001 (menos de R$ 0,01 por lançamento)
- Volume estimado: 1 foto/dia = ~R$ 0,20/mês

Irrelevante. Pode usar sem preocupação.
