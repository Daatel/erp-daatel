# components/selecao/queries.py
# Queries SQL centralizadas do Módulo de Seleção (Empório do Alho)

# 1. Lista de selecionadoras ativas
SQL_SELECIONADORAS_ATIVAS = """
SELECT 
    f.id, 
    f.nome, 
    f.regime_contratacao as vinculo, 
    COALESCE(f.nivel_classificacao, 'B') as nivel_classificacao,
    COALESCE(mn.meta_kg_dia, 70.0) as meta_kg_dia
FROM funcionarios f
LEFT JOIN selecao_metas_nivel mn ON mn.nivel = COALESCE(f.nivel_classificacao, 'B')
WHERE (f.cargo LIKE '%Selecionador%' OR f.cargo LIKE '%Catador%' OR f.cargo LIKE '%Operário%' OR f.cargo LIKE '%Operario%')
  AND f.status = 'ATIVO'
ORDER BY f.nome;
"""

# 2. Metas por nível
SQL_METAS_NIVEL = """
SELECT nivel, meta_kg_dia, descricao 
FROM selecao_metas_nivel 
ORDER BY nivel;
"""

SQL_UPSERT_META_NIVEL = """
INSERT INTO selecao_metas_nivel (nivel, meta_kg_dia, descricao, atualizado_em)
VALUES (?, ?, ?, CURRENT_TIMESTAMP)
ON CONFLICT (nivel) DO UPDATE SET
    meta_kg_dia = EXCLUDED.meta_kg_dia,
    descricao = EXCLUDED.descricao,
    atualizado_em = CURRENT_TIMESTAMP;
"""

# 3. Parâmetros mensais
SQL_PARAMETROS_MES = """
SELECT id, mes_ano, meta_diaria_casa_kg, dias_uteis_calculados, dias_uteis_efetivos
FROM selecao_parametros
WHERE strftime('%Y-%m-01', mes_ano) = strftime('%Y-%m-01', ?) OR mes_ano = ?;
"""

SQL_UPSERT_PARAMETROS = """
INSERT INTO selecao_parametros (mes_ano, meta_diaria_casa_kg, dias_uteis_calculados, dias_uteis_efetivos, atualizado_em)
VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
ON CONFLICT (mes_ano) DO UPDATE SET
    meta_diaria_casa_kg = EXCLUDED.meta_diaria_casa_kg,
    dias_uteis_calculados = EXCLUDED.dias_uteis_calculados,
    dias_uteis_efetivos = EXCLUDED.dias_uteis_efetivos,
    atualizado_em = CURRENT_TIMESTAMP;
"""

# 4. Exceções de calendário
SQL_EXCECOES_MES = """
SELECT id, data, tipo, descricao
FROM selecao_excecoes_calendario
ORDER BY data;
"""

SQL_INSERIR_EXCECAO = """
INSERT INTO selecao_excecoes_calendario (data, tipo, descricao)
VALUES (?, ?, ?)
ON CONFLICT (data) DO UPDATE SET
    tipo = EXCLUDED.tipo,
    descricao = EXCLUDED.descricao;
"""

SQL_REMOVER_EXCECAO = """
DELETE FROM selecao_excecoes_calendario WHERE id = ?;
"""

# 5. Presenças do dia
SQL_LIMPAR_PRESENCA_DIA = """
DELETE FROM selecao_presenca_diaria WHERE data = ?;
"""

SQL_INSERIR_PRESENCA = """
INSERT INTO selecao_presenca_diaria (data, selecionadora_id, confirmado_por)
VALUES (?, ?, ?);
"""

SQL_PRESENCAS_DO_DIA = """
SELECT 
    pd.selecionadora_id,
    f.nome,
    f.regime_contratacao as vinculo,
    COALESCE(f.nivel_classificacao, 'B') as nivel_classificacao,
    COALESCE(mn.meta_kg_dia, 70.0) as meta_kg_dia
FROM selecao_presenca_diaria pd
JOIN funcionarios f ON f.id = pd.selecionadora_id
LEFT JOIN selecao_metas_nivel mn ON mn.nivel = COALESCE(f.nivel_classificacao, 'B')
WHERE pd.data = ?
ORDER BY f.nome;
"""

# 6. Pesagens individuais
SQL_UPSERT_PESAGEM = """
INSERT INTO selecao_pesagens_diarias (data, selecionadora_id, peso_kg, meta_esperada_kg, lancado_por)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (data, selecionadora_id) DO UPDATE SET
    peso_kg = EXCLUDED.peso_kg,
    meta_esperada_kg = EXCLUDED.meta_esperada_kg,
    lancado_por = EXCLUDED.lancado_por,
    lancado_em = CURRENT_TIMESTAMP;
"""

SQL_PESAGENS_DO_DIA = """
SELECT pd.selecionadora_id, f.nome, pd.peso_kg, pd.meta_esperada_kg
FROM selecao_pesagens_diarias pd
JOIN funcionarios f ON f.id = pd.selecionadora_id
WHERE pd.data = ?;
"""

# 7. Balanço de aproveitamento do lote
SQL_UPSERT_APROVEITAMENTO = """
INSERT INTO selecao_aproveitamento_diario (data, peso_nobre_kg, peso_segunda_linha_kg, peso_descarte_kg, lancado_por)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (data) DO UPDATE SET
    peso_nobre_kg = EXCLUDED.peso_nobre_kg,
    peso_segunda_linha_kg = EXCLUDED.peso_segunda_linha_kg,
    peso_descarte_kg = EXCLUDED.peso_descarte_kg,
    lancado_por = EXCLUDED.lancado_por,
    lancado_em = CURRENT_TIMESTAMP;
"""

SQL_APROVEITAMENTO_DO_DIA = """
SELECT peso_nobre_kg, peso_segunda_linha_kg, peso_descarte_kg
FROM selecao_aproveitamento_diario
WHERE data = ?;
"""

# 8. Produção diária do mês para o BI
SQL_BI_PRODUCAO_MES = """
SELECT 
    pd.data,
    SUM(pd.peso_kg) as producao_total_kg,
    COUNT(DISTINCT pd.selecionadora_id) as n_presentes,
    AVG(pd.peso_kg) as media_por_selecionadora_kg
FROM selecao_pesagens_diarias pd
WHERE strftime('%Y-%m', pd.data) = ? OR pd.data LIKE ?
GROUP BY pd.data
ORDER BY pd.data;
"""
