# selecao/queries.py
# Todas as queries SQL do módulo de seleção
# Usar com st.connection ou supabase client conforme padrão do projeto

# -----------------------------------------------------------------------------
# SELECIONADORAS
# -----------------------------------------------------------------------------

SQL_SELECIONADORAS_ATIVAS = """
SELECT
  p.id,
  p.nome,
  p.vinculo,
  p.nivel_classificacao,
  mn.meta_kg_dia
FROM pessoas p
JOIN selecao_metas_nivel mn ON mn.nivel = p.nivel_classificacao
WHERE p.cargo = 'Selecionadora'
  AND p.status_ativa = TRUE
ORDER BY p.nome;
"""

# -----------------------------------------------------------------------------
# PRESENÇA
# -----------------------------------------------------------------------------

SQL_INSERIR_PRESENCA = """
INSERT INTO selecao_presenca_diaria (data, selecionadora_id, confirmado_por)
VALUES (:data, :selecionadora_id, :usuario_id)
ON CONFLICT (data, selecionadora_id) DO NOTHING;
"""

SQL_LIMPAR_PRESENCA_DIA = """
DELETE FROM selecao_presenca_diaria
WHERE data = :data;
"""

SQL_PRESENCAS_DO_DIA = """
SELECT
  p.id,
  p.nome,
  p.nivel_classificacao,
  mn.meta_kg_dia,
  COALESCE(pd.peso_kg, 0) AS peso_lancado
FROM selecao_presenca_diaria sp
JOIN pessoas p ON p.id = sp.selecionadora_id
JOIN selecao_metas_nivel mn ON mn.nivel = p.nivel_classificacao
LEFT JOIN selecao_pesagens_diarias pd
  ON pd.selecionadora_id = sp.selecionadora_id AND pd.data = sp.data
WHERE sp.data = :data
ORDER BY p.nome;
"""

# -----------------------------------------------------------------------------
# PESAGENS
# -----------------------------------------------------------------------------

SQL_UPSERT_PESAGEM = """
INSERT INTO selecao_pesagens_diarias
  (data, selecionadora_id, peso_kg, meta_esperada_kg, lancado_por)
VALUES
  (:data, :selecionadora_id, :peso_kg, :meta_esperada_kg, :usuario_id)
ON CONFLICT (data, selecionadora_id)
DO UPDATE SET
  peso_kg          = EXCLUDED.peso_kg,
  meta_esperada_kg = EXCLUDED.meta_esperada_kg,
  lancado_por      = EXCLUDED.lancado_por,
  lancado_em       = NOW();
"""

# -----------------------------------------------------------------------------
# APROVEITAMENTO DO LOTE
# -----------------------------------------------------------------------------

SQL_UPSERT_APROVEITAMENTO = """
INSERT INTO selecao_aproveitamento_diario
  (data, peso_nobre_kg, peso_segunda_linha_kg, peso_descarte_kg, lancado_por)
VALUES
  (:data, :peso_nobre_kg, :peso_segunda_linha_kg, :peso_descarte_kg, :usuario_id)
ON CONFLICT (data)
DO UPDATE SET
  peso_nobre_kg         = EXCLUDED.peso_nobre_kg,
  peso_segunda_linha_kg = EXCLUDED.peso_segunda_linha_kg,
  peso_descarte_kg      = EXCLUDED.peso_descarte_kg,
  lancado_por           = EXCLUDED.lancado_por,
  lancado_em            = NOW();
"""

SQL_APROVEITAMENTO_DO_DIA = """
SELECT
  peso_nobre_kg,
  peso_segunda_linha_kg,
  peso_descarte_kg,
  (peso_nobre_kg + peso_segunda_linha_kg + peso_descarte_kg) AS peso_total_kg
FROM selecao_aproveitamento_diario
WHERE data = :data;
"""

# -----------------------------------------------------------------------------
# BI — PAINEL DE PRODUÇÃO
# -----------------------------------------------------------------------------

SQL_PRODUCAO_DIARIA_MES = """
SELECT
  pd.data,
  SUM(pd.peso_kg)                                          AS producao_total_kg,
  COUNT(pd.selecionadora_id)                               AS n_presentes,
  ROUND(SUM(pd.peso_kg) / NULLIF(COUNT(*), 0), 1)         AS media_por_selecionadora_kg
FROM selecao_pesagens_diarias pd
WHERE DATE_TRUNC('month', pd.data) = :mes_ano
GROUP BY pd.data
ORDER BY pd.data;
"""

SQL_KPIS_MES = """
WITH dados_mes AS (
  SELECT
    SUM(peso_kg)              AS realizado_kg,
    COUNT(DISTINCT data)      AS dias_trabalhados,
    ROUND(AVG(
      CASE WHEN meta_esperada_kg > 0
           THEN peso_kg / meta_esperada_kg * 100
           ELSE 0 END
    ), 1)                     AS media_atingimento_pct
  FROM selecao_pesagens_diarias
  WHERE DATE_TRUNC('month', data) = :mes_ano
),
dias_acima AS (
  SELECT COUNT(*) AS dias_ok
  FROM (
    SELECT data
    FROM selecao_pesagens_diarias
    WHERE DATE_TRUNC('month', data) = :mes_ano
    GROUP BY data
    HAVING SUM(peso_kg) >= (
      SELECT meta_diaria_casa_kg FROM selecao_parametros
      WHERE mes_ano = :mes_ano
    )
  ) sub
),
params AS (
  SELECT
    meta_diaria_casa_kg,
    dias_uteis_efetivos,
    (meta_diaria_casa_kg * dias_uteis_efetivos) AS meta_mensal_kg
  FROM selecao_parametros
  WHERE mes_ano = :mes_ano
)
SELECT
  COALESCE(d.realizado_kg, 0)                           AS realizado_kg,
  p.meta_mensal_kg,
  p.meta_diaria_casa_kg,
  p.dias_uteis_efetivos,
  COALESCE(d.dias_trabalhados, 0)                       AS dias_trabalhados,
  COALESCE(da.dias_ok, 0)                               AS dias_acima_meta,
  COALESCE(d.media_atingimento_pct, 0)                  AS media_atingimento_pct,
  ROUND(
    COALESCE(d.realizado_kg, 0)
    / NULLIF(d.dias_trabalhados, 0)
    * p.dias_uteis_efetivos, 0
  )                                                     AS projetado_kg,
  ROUND(
    (p.meta_mensal_kg - COALESCE(d.realizado_kg, 0))
    / NULLIF(p.dias_uteis_efetivos - COALESCE(d.dias_trabalhados, 0), 0)
  , 0)                                                  AS necessario_por_dia_kg
FROM params p
LEFT JOIN dados_mes d ON TRUE
LEFT JOIN dias_acima da ON TRUE;
"""

SQL_MEDIA_PRESENTES_MES = """
SELECT
  ROUND(AVG(n_dia), 1) AS media_presentes_dia,
  ROUND(AVG(media_kg), 1) AS media_kg_por_selecionadora
FROM (
  SELECT
    data,
    COUNT(*)                                    AS n_dia,
    ROUND(SUM(peso_kg) / NULLIF(COUNT(*), 0), 1) AS media_kg
  FROM selecao_pesagens_diarias
  WHERE DATE_TRUNC('month', data) = :mes_ano
  GROUP BY data
) sub;
"""

# -----------------------------------------------------------------------------
# CONFIGURAÇÕES
# -----------------------------------------------------------------------------

SQL_METAS_NIVEL = """
SELECT nivel, meta_kg_dia, descricao
FROM selecao_metas_nivel
ORDER BY
  CASE nivel WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END;
"""

SQL_UPSERT_META_NIVEL = """
INSERT INTO selecao_metas_nivel (nivel, meta_kg_dia, descricao, atualizado_por)
VALUES (:nivel, :meta_kg_dia, :descricao, :usuario_id)
ON CONFLICT (nivel)
DO UPDATE SET
  meta_kg_dia   = EXCLUDED.meta_kg_dia,
  atualizado_em = NOW(),
  atualizado_por = EXCLUDED.atualizado_por;
"""

SQL_PARAMETROS_MES = """
SELECT
  meta_diaria_casa_kg,
  dias_uteis_calculados,
  dias_uteis_efetivos
FROM selecao_parametros
WHERE mes_ano = :mes_ano;
"""

SQL_UPSERT_PARAMETROS = """
INSERT INTO selecao_parametros
  (mes_ano, meta_diaria_casa_kg, dias_uteis_calculados, dias_uteis_efetivos)
VALUES
  (:mes_ano, :meta_diaria_casa_kg, :dias_uteis_calculados, :dias_uteis_efetivos)
ON CONFLICT (mes_ano)
DO UPDATE SET
  meta_diaria_casa_kg   = EXCLUDED.meta_diaria_casa_kg,
  dias_uteis_calculados = EXCLUDED.dias_uteis_calculados,
  dias_uteis_efetivos   = EXCLUDED.dias_uteis_efetivos,
  atualizado_em         = NOW();
"""

SQL_EXCECOES_MES = """
SELECT id, data, tipo, descricao
FROM selecao_excecoes_calendario
WHERE DATE_TRUNC('month', data) = :mes_ano
ORDER BY data;
"""

SQL_INSERIR_EXCECAO = """
INSERT INTO selecao_excecoes_calendario (data, tipo, descricao, criado_por)
VALUES (:data, :tipo, :descricao, :usuario_id)
ON CONFLICT (data) DO NOTHING;
"""

SQL_REMOVER_EXCECAO = """
DELETE FROM selecao_excecoes_calendario WHERE id = :id;
"""
