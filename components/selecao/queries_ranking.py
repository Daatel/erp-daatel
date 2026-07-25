# components/selecao/queries_ranking.py
# Queries SQL para Ranking e Histórico Individual de Selecionadoras (Empório do Alho)

SQL_RANKING_SELECIONADORAS = """
WITH periodo AS (
  SELECT
    f.id,
    f.nome,
    f.regime_contratacao as vinculo,
    COALESCE(f.nivel_classificacao, 'B') as nivel_classificacao,
    COALESCE(mn.meta_kg_dia, 70.0) AS meta_kg_dia,
    COUNT(DISTINCT pd.data)                               AS dias_presentes,
    COALESCE(SUM(pd.peso_kg), 0)                         AS producao_total_kg,
    COALESCE(AVG(pd.peso_kg), 0)                         AS media_dia_kg,
    COALESCE(AVG(pd.peso_kg / NULLIF(pd.meta_esperada_kg, 0) * 100), 0) AS media_atingimento_pct
  FROM funcionarios f
  LEFT JOIN selecao_metas_nivel mn ON mn.nivel = COALESCE(f.nivel_classificacao, 'B')
  LEFT JOIN selecao_pesagens_diarias pd ON pd.selecionadora_id = f.id AND pd.data >= ? AND pd.data <= ?
  WHERE f.cargo = 'Selecionador(a)'
    AND (f.status = 'ATIVO' OR f.status IS NULL)
  GROUP BY f.id, f.nome, f.regime_contratacao, f.nivel_classificacao, mn.meta_kg_dia
),
recente AS (
  SELECT selecionadora_id, AVG(peso_kg) AS media_recente
  FROM selecao_pesagens_diarias
  WHERE data >= ? AND data <= ?
  GROUP BY selecionadora_id
),
anterior AS (
  SELECT selecionadora_id, AVG(peso_kg) AS media_anterior
  FROM selecao_pesagens_diarias
  WHERE data >= ? AND data <= ?
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
  END AS tendencia
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
  (pd.peso_kg / NULLIF(pd.meta_esperada_kg, 0) * 100) AS pct_atingimento,
  ad.peso_nobre_kg,
  ad.peso_segunda_linha_kg,
  ad.peso_descarte_kg
FROM selecao_pesagens_diarias pd
LEFT JOIN selecao_aproveitamento_diario ad ON ad.data = pd.data
WHERE pd.selecionadora_id = ?
  AND pd.data >= ? AND pd.data <= ?
ORDER BY pd.data;
"""

SQL_PRESENCA_INDIVIDUAL = """
SELECT data
FROM selecao_presenca_diaria
WHERE selecionadora_id = ?
  AND data >= ? AND data <= ?
ORDER BY data;
"""
