# Adicionar ao queries.py existente

# -----------------------------------------------------------------------------
# RANKING DE SELECIONADORAS
# -----------------------------------------------------------------------------

SQL_RANKING_SELECIONADORAS = """
WITH periodo AS (
  SELECT
    p.id,
    p.nome,
    p.vinculo,
    p.nivel_classificacao,
    mn.meta_kg_dia,
    COUNT(DISTINCT pd.data)                               AS dias_presentes,
    COUNT(DISTINCT pr.data)                               AS dias_uteis_periodo,
    COALESCE(SUM(pd.peso_kg), 0)                         AS producao_total_kg,
    COALESCE(AVG(pd.peso_kg), 0)                         AS media_dia_kg,
    COALESCE(AVG(pd.peso_kg / NULLIF(pd.meta_esperada_kg, 0) * 100), 0)
                                                          AS media_atingimento_pct
  FROM pessoas p
  JOIN selecao_metas_nivel mn ON mn.nivel = p.nivel_classificacao
  LEFT JOIN selecao_pesagens_diarias pd
    ON pd.selecionadora_id = p.id
    AND pd.data BETWEEN :data_inicio AND :data_fim
  LEFT JOIN selecao_presenca_diaria pr
    ON pr.selecionadora_id = p.id
    AND pr.data BETWEEN :data_inicio AND :data_fim
  WHERE p.cargo = 'Selecionadora'
    AND p.status_ativa = TRUE
  GROUP BY p.id, p.nome, p.vinculo, p.nivel_classificacao, mn.meta_kg_dia
),
-- Tendência: últimos 15 dias vs 15 anteriores
recente AS (
  SELECT
    selecionadora_id,
    AVG(peso_kg) AS media_recente
  FROM selecao_pesagens_diarias
  WHERE data BETWEEN :data_meio AND :data_fim
  GROUP BY selecionadora_id
),
anterior AS (
  SELECT
    selecionadora_id,
    AVG(peso_kg) AS media_anterior
  FROM selecao_pesagens_diarias
  WHERE data BETWEEN :data_inicio AND :data_meio
  GROUP BY selecionadora_id
)
SELECT
  p.*,
  COALESCE(r.media_recente, 0)   AS media_recente_kg,
  COALESCE(a.media_anterior, 0)  AS media_anterior_kg,
  CASE
    WHEN a.media_anterior IS NULL OR a.media_anterior = 0 THEN 'neutro'
    WHEN r.media_recente > a.media_anterior * 1.05 THEN 'subindo'
    WHEN r.media_recente < a.media_anterior * 0.95 THEN 'caindo'
    ELSE 'estavel'
  END                            AS tendencia
FROM periodo p
LEFT JOIN recente r ON r.selecionadora_id = p.id
LEFT JOIN anterior a ON a.selecionadora_id = p.id
ORDER BY p.media_atingimento_pct DESC;
"""

SQL_HISTORICO_INDIVIDUAL = """
SELECT
  pd.data,
  pd.peso_kg,
  pd.meta_esperada_kg,
  ROUND(pd.peso_kg / NULLIF(pd.meta_esperada_kg, 0) * 100, 1) AS pct_atingimento,
  ad.peso_nobre_kg,
  ad.peso_segunda_linha_kg,
  ad.peso_descarte_kg
FROM selecao_pesagens_diarias pd
LEFT JOIN selecao_aproveitamento_diario ad ON ad.data = pd.data
WHERE pd.selecionadora_id = :selecionadora_id
  AND pd.data BETWEEN :data_inicio AND :data_fim
ORDER BY pd.data;
"""

SQL_PRESENCA_INDIVIDUAL = """
SELECT data
FROM selecao_presenca_diaria
WHERE selecionadora_id = :selecionadora_id
  AND data BETWEEN :data_inicio AND :data_fim
ORDER BY data;
"""
