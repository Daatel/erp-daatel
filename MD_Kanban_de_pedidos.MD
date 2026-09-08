{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1046{\fonttbl{\f0\fnil\fcharset0 Calibri;}{\f1\fnil Calibri;}{\f2\fnil\fcharset1 Cambria Math;}{\f3\fnil\fcharset0 Cambria Math;}{\f4\fnil Cambria Math;}}
{\colortbl ;\red0\green0\blue255;}
{\*\generator Riched20 10.0.19041}{\*\mmathPr\mmathFont2\mwrapIndent1440 }\viewkind4\uc1 
\pard\sa200\sl276\slmult1\f0\fs22\lang22 # Especifica\'e7\'e3o \f1\emdash  Fluxo de Repasse F\f0\'e1brica \f2\u8594?\f0  Horta do Pr\'edncipe \f2\u8594?\f0  Atacad\'e3o\par
\par
## 0. Contextualiza\'e7\'e3o da opera\'e7\'e3o\par
\par
A Emp\'f3rio do Alho possui uma parceria comercial (joint venture) com o distribuidor Horta do Pr\'edncipe, estruturada para viabilizar o atendimento a grandes redes de atacarejo, como o Atacad\'e3o, sem que a F\'e1brica precise assumir diretamente o relacionamento comercial, log\'edstico e financeiro com esse cliente.\par
\par
Nessa opera\'e7\'e3o, o Atacad\'e3o n\'e3o compra diretamente da F\'e1brica. Em vez disso, ele envia periodicamente uma grade de pedidos \f1\emdash  um lote que pode conter mais de 25 pedidos individuais, cada um vinculado a uma filial espec\f0\'edfica do Atacad\'e3o \f1\emdash  para a Horta do Pr\f0\'edncipe, que atua como o distribuidor formal perante o Atacad\'e3o. A Horta assume a responsabilidade comercial por esse cliente: emite a nota fiscal de venda, realiza a entrega e responde pela cobran\'e7a.\par
\par
Como a Horta n\'e3o fabrica o produto, ela depende da Emp\'f3rio do Alho para suprir cada um desses pedidos. A F\'e1brica, por sua vez, fatura e entrega para a Horta \f1\emdash  n\f0\'e3o para o Atacad\'e3o diretamente \f1\emdash  configurando o que se chama de pedido casado: um pedido interno da F\f0\'e1brica que existe unicamente para viabilizar um pedido espec\'edfico dentro da grade do Atacad\'e3o.\par
\par
A execu\'e7\'e3o da grade n\'e3o acontece de uma vez. Por limita\'e7\'f5es log\'edsticas e de rotas de entrega, os 25+ pedidos s\'e3o entregues aos poucos, no ritmo aproximado de 3 pedidos por dia, at\'e9 que a grade seja completamente atendida. Esse ritmo \'e9 combinado de forma manual e operacional, atrav\'e9s de um grupo de WhatsApp entre as partes envolvidas \f1\emdash  n\f0\'e3o h\'e1, hoje, uma regra autom\'e1tica de distribui\'e7\'e3o desse volume ao longo dos dias.\par
\par
Essa din\'e2mica cria uma depend\'eancia de sincronismo entre a F\'e1brica e a Horta: como a F\'e1brica precisa entregar o produto na Horta um dia \'fatil antes da data em que a Horta entregar\'e1 ao Atacad\'e3o, cada pedido casado carrega, na pr\'e1tica, duas datas relevantes \f1\emdash  a data de entrega da F\f0\'e1brica \'e0 Horta (o que aparece no planejamento de produ\'e7\'e3o) e a data de entrega da Horta ao Atacad\'e3o (que a origina).\par
\par
Do ponto de vista de gest\'e3o, isso gera uma necessidade espec\'edfica: mesmo que o pedido da F\'e1brica seja comercialmente faturado contra a Horta, \'e9 indispens\'e1vel manter a rastreabilidade de qual pedido do Atacad\'e3o \f1\emdash  e de qual filial \emdash  aquele pedido casado est\f0\'e1, de fato, atendendo. Sem esse v\'ednculo, perde-se a capacidade de confer\'eancia cruzada com a Horta, de acompanhamento do progresso da grade como um todo, e de identifica\'e7\'e3o de eventuais diverg\'eancias ou atrasos dentro do lote.\par
\par
\'c9 para suprir essa necessidade que se prop\'f5e a cria\'e7\'e3o de campos estruturados no cadastro de pedido, al\'e9m da defini\'e7\'e3o de uma regra padronizada de composi\'e7\'e3o das observa\'e7\'f5es da nota fiscal emitida para a Horta do Pr\'edncipe, detalhadas a seguir.\par
\par
## 1. Contexto\par
\par
A Emp\'f3rio do Alho mant\'e9m uma joint venture comercial com o distribuidor **Horta do Pr\'edncipe**. Nesse arranjo:\par
\par
1. O **Atacad\'e3o** envia uma grade \'fanica de pedidos (25+ pedidos) para serem entregues em lotes, no ritmo de aproximadamente 3 pedidos/dia \f1\emdash  ritmo definido manualmente pela log\f0\'edstica de rotas, alinhado em grupo de WhatsApp (sem automa\'e7\'e3o de distribui\'e7\'e3o no sistema).\par
2. A **F\'e1brica fatura e entrega para a Horta do Pr\'edncipe** um dia \'fatil antes de cada entrega programada ao Atacad\'e3o (pedido casado).\par
3. A **Horta do Pr\'edncipe refatura para o Atacad\'e3o**, realiza a entrega final e fica respons\'e1vel pela cobran\'e7a junto ao Atacad\'e3o.\par
\par
O pedido que a F\'e1brica gerencia no ERP (faturado contra a Horta) precisa carregar a rastreabilidade do pedido de origem do Atacad\'e3o, para permitir gest\'e3o conjunta com a Horta e confer\'eancia cruzada quando necess\'e1rio.\par
\par
## 2. Novos campos no cadastro de pedido\par
\par
Aplic\'e1veis apenas quando o pedido for identificado como **pedido casado / repasse** (cliente de faturamento = Horta do Pr\'edncipe).\par
\par
| Campo | Tipo | Obrigat\'f3rio | Descri\'e7\'e3o |\par
|---|---|---|---|\par
| `flag\f3 _\f0 op\f3 _\f0 casada` | boolean | Sim | Marca o pedido como parte do fluxo de repasse via Horta do Pr\'edncipe. Controla a exibi\'e7\'e3o dos campos abaixo e o destaque visual no Kanban. |\par
| `grade_id` | texto/c\'f3digo | Sim, se `flag_op_casada= true` | Identifica o lote/grade do Atacad\'e3o ao qual o pedido pertence (ex: `GRADE-012`). Permite acompanhar quantos dos pedidos da grade j\'e1 foram faturados/entregues. |\par
| `pedido_atacadao_numero` | texto | Sim, se `flag_op_casada= true` | N\'famero do pedido original do Atacad\'e3o dentro da grade. |\par
| `filial_atacadao` | texto | Sim, se `flag_op_casada= true` | C\'f3digo ou nome da filial do Atacad\'e3o que receber\'e1 o produto final via Horta. |\par
\par
**Observa\'e7\'f5es de implementa\'e7\'e3o:**\par
- Esses campos ficam no pr\'f3prio registro do pedido da F\'e1brica (n\'e3o em uma tabela separada), pois o pedido em si \'e9 a unidade de rastreabilidade.\par
- `grade_id` n\'e3o precisa de cadastro pr\'e9vio de "grade" como entidade separada na V1 \f1\emdash  pode ser um campo de texto livre padronizado (ex: sempre `GRADE-` + n\f0\'famero). Uma tela de acompanhamento por grade (contagem de pedidos entregues/pendentes) pode ser um incremento futuro, n\'e3o bloqueante para o MVP.\par
- A data de entrega deste pedido (usada no Kanban de produ\'e7\'e3o) \'e9 sempre **D-1 \'fatil** em rela\'e7\'e3o \'e0 data combinada de entrega da Horta ao Atacad\'e3o \f1\emdash  mas essa data continua sendo definida manualmente por quem cadastra o pedido, n\f0\'e3o calculada automaticamente, j\'e1 que o ritmo vem do alinhamento externo via WhatsApp.\par
\par
## 3. Regra de faturamento \f1\emdash  Observa\f0\'e7\'f5es da Nota Fiscal\par
\par
Quando `flag_op_casada= true`, a emiss\'e3o da Nota Fiscal para a Horta do Pr\'edncipe deve concatenar automaticamente os campos de rastreabilidade no campo **Informa\'e7\'f5es Complementares / Observa\'e7\'f5es** da NF, seguindo o padr\'e3o:\par
\par
```\par
Grade \{grade_id\} \'b7 Pedido Atacad\'e3o \{pedido_atacadao_numero\} \'b7 Filial \{filial_atacadao\}\par
```\par
\par
**Exemplo:**\par
```\par
Grade GRADE-012 \'b7 Pedido Atacad\'e3o 88231 \'b7 Filial Niter\'f3i\par
```\par
\par
**Por que gerar isso automaticamente, e n\'e3o depender de digita\'e7\'e3o manual:**\par
- Elimina risco de erro de digita\'e7\'e3o ou diverg\'eancia de padr\'e3o entre notas.\par
- Garante que a informa\'e7\'e3o de rastreabilidade sempre chegue \'e0 Horta do Pr\'edncipe de forma padronizada, mesmo que ningu\'e9m lembre de preencher manualmente.\par
- Os campos estruturados (`grade_id`, `pedido_atacadao_numero`, `filial_atacadao`) continuam existindo no banco independentemente do texto gerado na Obs \f1\emdash  a Obs \f0\'e9 apenas uma *representa\'e7\'e3o* desses dados para fins fiscais/operacionais, nunca a fonte da informa\'e7\'e3o. Isso evita depender de parsing de texto livre para qualquer relat\'f3rio ou consulta futura (ex: "quantos pedidos da Grade 12 j\'e1 foram faturados").\par
\par
## 4. Representa\'e7\'e3o no Kanban de produ\'e7\'e3o\par
\par
Para pedidos com `flag_op_casada= true`, o card no Kanban deve exibir:\par
\par
- Nome do cliente de faturamento: **Horta do Pr\'edncipe**, com tag visual de destaque (ex: \'edcone/etiqueta "repasse")\par
- Linha secund\'e1ria com a rastreabilidade resumida: `Grade \{grade_id\} \'b7 Ped. \{pedido_atacadao_numero\} \'b7 Filial \{filial_atacadao\}`\par
- Demais campos do card (produto, quantidade, valor) seguem o padr\'e3o j\'e1 definido para os demais pedidos\par
\par
## 5. Fora do escopo desta especifica\'e7\'e3o\par
\par
- Automa\'e7\'e3o de distribui\'e7\'e3o do ritmo de entregas (3/dia) \f1\emdash  permanece manual/combinado externamente.\par
- Tela de acompanhamento consolidado por grade (ex: dashboard "8 de 25 entregues") \emdash  pode ser um m\f0\'f3dulo futuro (BI ou painel simples) constru\'eddo sobre os campos estruturados aqui definidos.\par
- Regra de cobran\'e7a/concilia\'e7\'e3o entre F\'e1brica e Horta \f1\emdash  este documento cobre apenas cadastro de pedido e emiss\f0\'e3o de NF.\par
\par
\par
\f3 # \f0 Implementa\'e7\'e3o\f3  \f4\emdash  Kanban de pedidos (Daatel / Supabase)\par
\f3\lang1046 Verificar representa\'e7\'e3o visual em kanban_pedidos_producao_v3.html nesta mesma pasta.\f4\par
Pacote completo pra colar no Antigravity e executar. \par
Segue a ordem sugerida \emdash  cada bloco depende do anterior.\par
\par
---\par
\par
## 0. Pr\f3\'e9-requisitos / vari\'e1veis de ambiente\par
\par
Confirmar que existem (ou criar) estes segredos:\par
\par
**No Supabase (Project Settings \f2\u8594? Edge Functions \u8594? Secrets):**\par
```\par
KANBAN_SHARED_SECRET=<gerar uma string aleat\'f3ria longa, ex: openssl rand -hex 32>\par
SUPABASE_SERVICE_ROLE_KEY=<j\'e1 existe no projeto, copiar de Settings \u8594? API>\par
SUPABASE_URL=<j\'e1 existe, copiar de Settings \u8594? API>\par
```\par
\par
**No Streamlit Cloud (Settings \u8594? Secrets, `st.secrets`):**\par
```toml\par
KANBAN_SHARED_SECRET = "<mesma string usada acima, tem que ser id\'eantica>"\par
SUPABASE_URL = "<mesma URL do projeto>"\par
SUPABASE_ANON_KEY = "<chave anon p\'fablica, Settings \u8594? API>"\par
```\par
\par
O `KANBAN_SHARED_SECRET` \'e9 o segredo que permite ao Streamlit assinar um token e \'e0 Edge Function validar esse token. Nunca vai pro navegador.\par
\par
---\par
\par
## 1. Altera\'e7\'f5es no banco (rodar no SQL Editor do Supabase)\par
\par
```sql\par
-- Campos novos na tabela pedidos\par
alter table pedidos\par
  add column if not exists data_prevista date,\par
  add column if not exists updated_at timestamptz not null default now(),\par
  add column if not exists flag_op_casada boolean not null default false,\par
  add column if not exists grade_id text,\par
  add column if not exists pedido_atacadao_numero text,\par
  add column if not exists filial_atacadao text;\par
\par
-- Trigger para manter updated_at sempre atualizado em qualquer UPDATE\par
create or replace function set_updated_at()\par
returns trigger as $$\par
begin\par
  new.updated_at = now();\par
  return new;\par
end;\par
$$ language plpgsql;\par
\par
drop trigger if exists trg_pedidos_updated_at on pedidos;\par
create trigger trg_pedidos_updated_at\par
  before update on pedidos\par
  for each row\par
  execute function set_updated_at();\par
\par
-- Tabela de auditoria de reprograma\'e7\'e3o\par
create table if not exists log_reprogramacao (\par
  id bigserial primary key,\par
  pedido_id bigint not null references pedidos(id),\par
  data_anterior date,\par
  data_nova date,\par
  usuario text not null,\par
  criado_em timestamptz not null default now()\par
);\par
\par
-- Tabela de feriados (nacional + Rio), usada s\'f3 no front pra classificar colunas\par
create table if not exists feriados (\par
  data date primary key,\par
  descricao text\par
);\par
\par
-- Popular com os feriados nacionais fixos de 2026 (ajustar/completar conforme necess\'e1rio)\par
insert into feriados (data, descricao) values\par
  ('2026-01-01', 'Confraterniza\'e7\'e3o Universal'),\par
  ('2026-02-16', 'Carnaval'),\par
  ('2026-02-17', 'Carnaval'),\par
  ('2026-04-03', 'Sexta-feira Santa'),\par
  ('2026-04-21', 'Tiradentes'),\par
  ('2026-05-01', 'Dia do Trabalho'),\par
  ('2026-09-07', 'Independ\'eancia'),\par
  ('2026-10-12', 'Nossa Senhora Aparecida'),\par
  ('2026-11-02', 'Finados'),\par
  ('2026-11-15', 'Proclama\'e7\'e3o da Rep\'fablica'),\par
  ('2026-11-20', 'Consci\'eancia Negra'),\par
  ('2026-12-25', 'Natal'),\par
  ('2026-01-20', 'S\'e3o Sebasti\'e3o (munic\'edpio do Rio)'),\par
  ('2026-04-23', 'S\'e3o Jorge (munic\'edpio do Rio)')\par
on conflict (data) do nothing;\par
```\par
\par
**\'cdndice recomendado** (a query de listagem do Kanban vai filtrar/ordenar por isso):\par
```sql\par
create index if not exists idx_pedidos_data_prevista on pedidos (data_prevista);\par
```\par
\par
---\par
\par
## 2. Permiss\'f5es (RLS) \emdash  leitura liberada, escrita bloqueada\par
\par
O princ\'edpio: o navegador s\'f3 pode **ler**. Toda escrita passa pela Edge Function, que usa a `service_role` (que ignora RLS).\par
\par
```sql\par
alter table pedidos enable row level security;\par
\par
-- Leitura liberada para o front (ajustar 'anon' para 'authenticated' se preferir exigir login Supabase)\par
drop policy if exists "kanban_select_pedidos" on pedidos;\par
create policy "kanban_select_pedidos"\par
  on pedidos for select\par
  to anon\par
  using (true);\par
\par
-- Ningu\'e9m al\'e9m da service_role pode escrever direto na tabela\par
revoke insert, update, delete on pedidos from anon, authenticated;\par
\par
alter table feriados enable row level security;\par
drop policy if exists "kanban_select_feriados" on feriados;\par
create policy "kanban_select_feriados"\par
  on feriados for select\par
  to anon\par
  using (true);\par
```\par
\par
---\par
\par
## 3. Edge Function \emdash  `mover-pedido`\par
\par
Criar em `supabase/functions/mover-pedido/index.ts`:\par
\par
```typescript\par
import \{ serve \} from "{{\field{\*\fldinst{HYPERLINK https://deno.land/std@0.224.0/http/server.ts }}{\fldrslt{https://deno.land/std@0.224.0/http/server.ts\ul0\cf0}}}}\f3\fs22 ";\par
import \{ createClient \} from "{{\field{\*\fldinst{HYPERLINK https://esm.sh/@supabase/supabase-js@2 }}{\fldrslt{https://esm.sh/@supabase/supabase-js@2\ul0\cf0}}}}\f3\fs22 ";\par
import \{ create, verify, getNumericDate \} from "{{\field{\*\fldinst{HYPERLINK https://deno.land/x/djwt@v3.0.2/mod.ts }}{\fldrslt{https://deno.land/x/djwt@v3.0.2/mod.ts\ul0\cf0}}}}\f3\fs22 ";\par
\par
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;\par
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;\par
const SHARED_SECRET = Deno.env.get("KANBAN_SHARED_SECRET")!;\par
\par
const corsHeaders = \{\par
  "Access-Control-Allow-Origin": "*",\par
  "Access-Control-Allow-Headers": "authorization, content-type",\par
  "Access-Control-Allow-Methods": "POST, OPTIONS",\par
\};\par
\par
async function getKey() \{\par
  return await crypto.subtle.importKey(\par
    "raw",\par
    new TextEncoder().encode(SHARED_SECRET),\par
    \{ name: "HMAC", hash: "SHA-256" \},\par
    false,\par
    ["sign", "verify"],\par
  );\par
\}\par
\par
serve(async (req) => \{\par
  if (req.method === "OPTIONS") \{\par
    return new Response("ok", \{ headers: corsHeaders \});\par
  \}\par
\par
  try \{\par
    const authHeader = req.headers.get("Authorization") ?? "";\par
    const token = authHeader.replace("Bearer ", "");\par
    if (!token) \{\par
      return new Response(JSON.stringify(\{ erro: "token ausente" \}), \{\par
        status: 401,\par
        headers: corsHeaders,\par
      \});\par
    \}\par
\par
    const key = await getKey();\par
    let payload;\par
    try \{\par
      payload = await verify(token, key);\par
    \} catch \{\par
      return new Response(JSON.stringify(\{ erro: "token inv\'e1lido ou expirado" \}), \{\par
        status: 401,\par
        headers: corsHeaders,\par
      \});\par
    \}\par
\par
    const \{ pedido_id, nova_data_prevista, updated_at_esperado \} = await req.json();\par
\par
    if (!pedido_id || nova_data_prevista === undefined) \{\par
      return new Response(JSON.stringify(\{ erro: "par\'e2metros faltando" \}), \{\par
        status: 400,\par
        headers: corsHeaders,\par
      \});\par
    \}\par
\par
    const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);\par
\par
    const \{ data: pedidoAtual, error: erroBusca \} = await supabase\par
      .from("pedidos")\par
      .select("data_prevista, updated_at")\par
      .eq("id", pedido_id)\par
      .single();\par
\par
    if (erroBusca || !pedidoAtual) \{\par
      return new Response(JSON.stringify(\{ erro: "pedido n\'e3o encontrado" \}), \{\par
        status: 404,\par
        headers: corsHeaders,\par
      \});\par
    \}\par
\par
    if (\par
      updated_at_esperado &&\par
      new Date(pedidoAtual.updated_at).getTime() !== new Date(updated_at_esperado).getTime()\par
    ) \{\par
      return new Response(\par
        JSON.stringify(\{ erro: "conflito: pedido foi alterado por outra pessoa, recarregue o card" \}),\par
        \{ status: 409, headers: corsHeaders \},\par
      );\par
    \}\par
\par
    const \{ error: erroUpdate \} = await supabase\par
      .from("pedidos")\par
      .update(\{ data_prevista: nova_data_prevista \})\par
      .eq("id", pedido_id);\par
\par
    if (erroUpdate) \{\par
      return new Response(JSON.stringify(\{ erro: erroUpdate.message \}), \{\par
        status: 500,\par
        headers: corsHeaders,\par
      \});\par
    \}\par
\par
    await supabase.from("log_reprogramacao").insert(\{\par
      pedido_id,\par
      data_anterior: pedidoAtual.data_prevista,\par
      data_nova: nova_data_prevista,\par
      usuario: (payload as any).usuario ?? "desconhecido",\par
    \});\par
\par
    return new Response(JSON.stringify(\{ ok: true \}), \{\par
      status: 200,\par
      headers: corsHeaders,\par
    \});\par
  \} catch (e) \{\par
    return new Response(JSON.stringify(\{ erro: String(e) \}), \{\par
      status: 500,\par
      headers: corsHeaders,\par
    \});\par
  \}\par
\});\par
```\par
\par
**Deploy:**\par
```bash\par
supabase functions deploy mover-pedido --no-verify-jwt\par
```\par
(`--no-verify-jwt` porque a valida\'e7\'e3o \'e9 feita manualmente com o `KANBAN_SHARED_SECRET`, n\'e3o com o Supabase Auth padr\'e3o.)\par
\par
---\par
\par
## 4. Gera\'e7\'e3o do token no Streamlit (Python)\par
\par
Criar `auth_kanban.py`:\par
\par
```python\par
import streamlit as st\par
from datetime import datetime, timedelta, timezone\par
import jwt  # pip install pyjwt\par
\par
def gerar_token_kanban(usuario: str, minutos_validade: int = 15) -> str:\par
    payload = \{\par
        "usuario": usuario,\par
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutos_validade),\par
    \}\par
    return jwt.encode(payload, st.secrets["KANBAN_SHARED_SECRET"], algorithm="HS256")\par
```\par
\par
Observa\'e7\'e3o: a lib `djwt` (Deno) e `PyJWT` (Python) s\'e3o compat\'edveis para HS256 \emdash  o token gerado em um \'e9 validado no outro sem convers\'e3o.\par
\par
---\par
\par
## 5. M\'f3dulo compartilhado de dias \'fateis (JavaScript, usado no Kanban)\par
\par
Criar `dias_uteis.js` (carregado dentro do HTML embutido):\par
\par
```javascript\par
function formatarData(date) \{\par
  return date.toISOString().split("T")[0];\par
\}\par
\par
function ehDiaUtil(date, feriadosSet) \{\par
  const diaSemana = date.getDay();\par
  if (diaSemana === 0 || diaSemana === 6) return false;\par
  if (feriadosSet.has(formatarData(date))) return false;\par
  return true;\par
\}\par
\par
function proximosDiasUteis(quantidade, feriadosSet, aPartirDe = new Date()) \{\par
  const dias = [];\par
  let cursor = new Date(aPartirDe);\par
  cursor.setDate(cursor.getDate() + 1);\par
  while (dias.length < quantidade) \{\par
    if (ehDiaUtil(cursor, feriadosSet)) \{\par
      dias.push(new Date(cursor));\par
    \}\par
    cursor.setDate(cursor.getDate() + 1);\par
  \}\par
  return dias;\par
\}\par
\par
// Classifica um pedido em uma das colunas do Kanban\par
function classificarPedido(pedido, feriadosSet, hoje = new Date()) \{\par
  const hojeStr = formatarData(hoje);\par
\par
  if (!pedido.data_prevista) \{\par
    return \{ coluna: "sem_data" \};\par
  \}\par
\par
  if (pedido.data_prevista < hojeStr) \{\par
    const diasAtraso = Math.floor(\par
      (hoje - new Date(pedido.data_prevista)) / (1000 * 60 * 60 * 24),\par
    );\par
    return \{ coluna: "atrasado", diasAtraso \};\par
  \}\par
\par
  const janela = proximosDiasUteis(5, feriadosSet, hoje);\par
  const indice = janela.findIndex((d) => formatarData(d) === pedido.data_prevista);\par
\par
  if (indice >= 0) \{\par
    return \{ coluna: `dia_$\{indice\}`, data: janela[indice] \};\par
  \}\par
\par
  return \{ coluna: "alem" \};\par
\}\par
```\par
\par
---\par
\par
## 6. Kanban \emdash  leitura e escrita (JavaScript, dentro do HTML embutido)\par
\par
> **OBS PARA O AG (Antigravity): ajustar antes de implementar.**\par
> Os nomes de coluna `cliente`, `valor`, `produto`, `quantidade` usados no `select` abaixo s\'e3o placeholders. Antes de implementar, consultar o schema real da tabela `pedidos` no Supabase e substituir pelos nomes de coluna efetivamente usados no projeto (ex: pode j\'e1 existir `cliente_nome`, `valor_total`, `descricao_produto`, etc.). O mesmo vale para qualquer outro trecho deste documento que referencie nomes de coluna do pedido \emdash  a lista de campos novos na se\'e7\'e3o 1 (`data_prevista`, `updated_at`, `flag_op_casada`, `grade_id`, `pedido_atacadao_numero`, `filial_atacadao`) s\'e3o os \'fanicos nomes que devem ser criados exatamente como est\'e3o; os demais devem ser conferidos contra o schema existente.\par
\par
```javascript\par
const SUPABASE_URL = "__SUPABASE_URL__";\par
const SUPABASE_ANON_KEY = "__SUPABASE_ANON_KEY__";\par
const TOKEN_KANBAN = "__TOKEN__"; // gerado pelo Streamlit a cada render\par
\par
async function carregarPedidos() \{\par
  const resp = await fetch(\par
    `$\{SUPABASE_URL\}/rest/v1/pedidos?select=id,cliente,valor,produto,quantidade,data_prevista,updated_at,flag_op_casada,grade_id,pedido_atacadao_numero,filial_atacadao&order=data_prevista.asc`,\par
    \{\par
      headers: \{\par
        apikey: SUPABASE_ANON_KEY,\par
        Authorization: `Bearer $\{SUPABASE_ANON_KEY\}`,\par
      \},\par
    \},\par
  );\par
  return await resp.json();\par
\}\par
\par
async function carregarFeriados() \{\par
  const resp = await fetch(`$\{SUPABASE_URL\}/rest/v1/feriados?select=data`, \{\par
    headers: \{\par
      apikey: SUPABASE_ANON_KEY,\par
      Authorization: `Bearer $\{SUPABASE_ANON_KEY\}`,\par
    \},\par
  \});\par
  const linhas = await resp.json();\par
  return new Set(linhas.map((l) => l.data));\par
\}\par
\par
async function moverPedido(pedidoId, novaData, updatedAtEsperado) \{\par
  const resp = await fetch(`$\{SUPABASE_URL\}/functions/v1/mover-pedido`, \{\par
    method: "POST",\par
    headers: \{\par
      "Content-Type": "application/json",\par
      Authorization: `Bearer $\{TOKEN_KANBAN\}`,\par
    \},\par
    body: JSON.stringify(\{\par
      pedido_id: pedidoId,\par
      nova_data_prevista: novaData,\par
      updated_at_esperado: updatedAtEsperado,\par
    \}),\par
  \});\par
  const resultado = await resp.json();\par
  if (!resp.ok) \{\par
    alert(resultado.erro || "Erro ao mover o pedido, tente novamente.");\par
    return false;\par
  \}\par
  return true;\par
\}\par
```\par
\par
**Drag-and-drop**: usar SortableJS (via CDN `cdnjs.cloudflare.com`) em cada coluna, disparando `moverPedido()` no evento `onEnd`. A l\'f3gica de re-render ap\'f3s sucesso: recarregar `carregarPedidos()` e redesenhar (mais simples e seguro do que tentar sincronizar estado local manualmente).\par
\par
---\par
\par
## 7. Integra\'e7\'e3o no Streamlit\par
\par
No arquivo da p\'e1gina do Kanban (ex: `pagina_kanban.py`):\par
\par
```python\par
import streamlit as st\par
import streamlit.components.v1 as components\par
from auth_kanban import gerar_token_kanban\par
\par
token = gerar_token_kanban(usuario=st.session_state["usuario_logado"])\par
\par
with open("kanban_widget.html", encoding="utf-8") as f:\par
    html_template = f.read()\par
\par
html_final = (\par
    html_template\par
    .replace("__SUPABASE_URL__", st.secrets["SUPABASE_URL"])\par
    .replace("__SUPABASE_ANON_KEY__", st.secrets["SUPABASE_ANON_KEY"])\par
    .replace("__TOKEN__", token)\par
)\par
\par
components.html(html_final, height=750, scrolling=True)\par
```\par
\par
O `kanban_widget.html` re\'fane o HTML/CSS j\'e1 validado no mockup (colunas, cards, avatares, chips 500g/1kg, checkbox de valor) + os scripts das se\'e7\'f5es 5 e 6.\par
\par
---\par
\par
## 8. Regra de neg\'f3cio \emdash  pedido casado (Horta do Pr\'edncipe)\par
\par
J\'e1 coberta em detalhe no documento `spec_pedidos_horta_principe.md`. Resumo de integra\'e7\'e3o aqui:\par
\par
- Campos `flag_op_casada`, `grade_id`, `pedido_atacadao_numero`, `filial_atacadao` j\'e1 v\'eam no schema da se\'e7\'e3o 1.\par
- Card do Kanban: se `flag_op_casada = true`, exibir tag "repasse" e a linha `Grade \{grade_id\} \'b7 Ped. \{pedido_atacadao_numero\} \'b7 Filial \{filial_atacadao\}`.\par
- Emiss\'e3o de NF (fora do escopo deste Kanban, mas documentado): concatenar os 3 campos automaticamente na Obs da nota fiscal emitida contra a Horta do Pr\'edncipe.\par
\par
---\par
\par
## 9. Checklist antes de considerar pronto\par
\par
- [ ] Rodar os SQLs das se\'e7\'f5es 1 e 2 no Supabase\par
- [ ] Configurar os 3 segredos no Supabase e os 3 no Streamlit Cloud (se\'e7\'e3o 0)\par
- [ ] Deploy da Edge Function `mover-pedido`\par
- [ ] Testar gera\'e7\'e3o de token no Python e valida\'e7\'e3o manual (`curl` com token expirado deve retornar 401)\par
- [ ] Testar `moverPedido()` com dois updates simult\'e2neos no mesmo pedido \f2\u8594? segundo deve retornar 409\par
- [ ] Confirmar que `revoke insert, update, delete` realmente bloqueia escrita direta via anon key (tentar um `PATCH` via REST direto, sem passar pela Edge Function \emdash  deve falhar)\par
- [ ] Validar classifica\'e7\'e3o de colunas com um pedido em cada situa\'e7\'e3o: sem data, atrasado, hoje, dentro dos 5 dias \'fateis, al\'e9m\par
- [ ] Validar caso de feriado no meio da janela de 5 dias \'fateis (n\'e3o deve contar como coluna)\par
- [ ] Testar um pedido com `flag_op_casada = true` e conferir se a tag e os campos aparecem certos no card\f0\par
}
 