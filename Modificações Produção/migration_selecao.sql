-- =============================================================================
-- MIGRATION: Módulo de Seleção, Metas e Rendimento de Alho
-- ERP Daatel / Empório do Alho
-- =============================================================================
-- ⚠️  RODAR EM TRANSAÇÃO. VERIFICAR CONFLITOS ANTES DE EXECUTAR.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. Alterações na tabela pessoas
-- -----------------------------------------------------------------------------

ALTER TABLE pessoas
  ADD COLUMN IF NOT EXISTS vinculo VARCHAR(10) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS nivel_classificacao VARCHAR(10) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS status_ativa BOOLEAN DEFAULT TRUE;

COMMENT ON COLUMN pessoas.vinculo IS 'CLT | Diarista — preenchido apenas para cargo Selecionadora';
COMMENT ON COLUMN pessoas.nivel_classificacao IS 'A | B | Teste — preenchido apenas para cargo Selecionadora';
COMMENT ON COLUMN pessoas.status_ativa IS 'TRUE = aparece nas listas operacionais; FALSE = arquivada';

-- -----------------------------------------------------------------------------
-- 2. Metas por nível
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS selecao_metas_nivel (
  nivel          VARCHAR(10)   PRIMARY KEY,
  meta_kg_dia    DECIMAL(8,2)  NOT NULL,
  descricao      VARCHAR(100)  NOT NULL,
  atualizado_em  TIMESTAMP     DEFAULT NOW(),
  atualizado_por INTEGER       REFERENCES pessoas(id)
);

INSERT INTO selecao_metas_nivel (nivel, meta_kg_dia, descricao) VALUES
  ('A',     90.00, 'Alta performance / assídua'),
  ('B',     70.00, 'Rendimento padrão'),
  ('Teste', 50.00, 'Em treinamento / avaliação')
ON CONFLICT (nivel) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. Parâmetros mensais
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS selecao_parametros (
  id                    SERIAL PRIMARY KEY,
  mes_ano               DATE          NOT NULL UNIQUE,
  meta_diaria_casa_kg   DECIMAL(8,2)  NOT NULL DEFAULT 500.00,
  dias_uteis_calculados INTEGER       NOT NULL DEFAULT 22,
  dias_uteis_efetivos   INTEGER       NOT NULL DEFAULT 22,
  atualizado_em         TIMESTAMP     DEFAULT NOW()
);

COMMENT ON COLUMN selecao_parametros.mes_ano IS 'Sempre o primeiro dia do mês: 2026-07-01';
COMMENT ON COLUMN selecao_parametros.dias_uteis_calculados IS 'Automático: dias do mês - sáb - dom';
COMMENT ON COLUMN selecao_parametros.dias_uteis_efetivos IS 'Após exceções (feriados removidos, sábados adicionados)';

-- -----------------------------------------------------------------------------
-- 4. Exceções de calendário
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS selecao_excecoes_calendario (
  id          SERIAL PRIMARY KEY,
  data        DATE          NOT NULL UNIQUE,
  tipo        VARCHAR(10)   NOT NULL CHECK (tipo IN ('REMOVER', 'ADICIONAR')),
  descricao   VARCHAR(100),
  criado_em   TIMESTAMP     DEFAULT NOW(),
  criado_por  INTEGER       REFERENCES pessoas(id)
);

COMMENT ON COLUMN selecao_excecoes_calendario.tipo IS 'REMOVER = feriado; ADICIONAR = sábado trabalhado';

-- -----------------------------------------------------------------------------
-- 5. Presença diária
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS selecao_presenca_diaria (
  id                SERIAL PRIMARY KEY,
  data              DATE      NOT NULL,
  selecionadora_id  INTEGER   NOT NULL REFERENCES pessoas(id),
  confirmado_por    INTEGER   REFERENCES pessoas(id),
  confirmado_em     TIMESTAMP DEFAULT NOW(),
  UNIQUE (data, selecionadora_id)
);

CREATE INDEX IF NOT EXISTS idx_presenca_data
  ON selecao_presenca_diaria (data);

-- -----------------------------------------------------------------------------
-- 6. Pesagens diárias
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS selecao_pesagens_diarias (
  id                SERIAL PRIMARY KEY,
  data              DATE          NOT NULL,
  selecionadora_id  INTEGER       NOT NULL REFERENCES pessoas(id),
  peso_kg           DECIMAL(8,2)  NOT NULL CHECK (peso_kg >= 0),
  meta_esperada_kg  DECIMAL(8,2)  NOT NULL,
  lancado_por       INTEGER       REFERENCES pessoas(id),
  lancado_em        TIMESTAMP     DEFAULT NOW(),
  UNIQUE (data, selecionadora_id)
);

CREATE INDEX IF NOT EXISTS idx_pesagem_data
  ON selecao_pesagens_diarias (data);

CREATE INDEX IF NOT EXISTS idx_pesagem_selecionadora
  ON selecao_pesagens_diarias (selecionadora_id, data);

-- -----------------------------------------------------------------------------
-- 7. Aproveitamento diário do lote
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS selecao_aproveitamento_diario (
  id                    SERIAL PRIMARY KEY,
  data                  DATE          NOT NULL UNIQUE,
  peso_nobre_kg         DECIMAL(8,2)  NOT NULL DEFAULT 0,
  peso_segunda_linha_kg DECIMAL(8,2)  NOT NULL DEFAULT 0,
  peso_descarte_kg      DECIMAL(8,2)  NOT NULL DEFAULT 0,
  lancado_por           INTEGER       REFERENCES pessoas(id),
  lancado_em            TIMESTAMP     DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 8. Histórico de nível por selecionadora
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS selecao_historico_nivel (
  id                SERIAL PRIMARY KEY,
  selecionadora_id  INTEGER       NOT NULL REFERENCES pessoas(id),
  nivel_anterior    VARCHAR(10),
  nivel_novo        VARCHAR(10)   NOT NULL,
  data_inicio       DATE          NOT NULL,
  data_fim          DATE,
  alterado_por      INTEGER       REFERENCES pessoas(id),
  alterado_em       TIMESTAMP     DEFAULT NOW()
);

COMMIT;

-- =============================================================================
-- ROLLBACK (guardar para emergência)
-- =============================================================================
/*
BEGIN;
DROP TABLE IF EXISTS selecao_historico_nivel;
DROP TABLE IF EXISTS selecao_aproveitamento_diario;
DROP TABLE IF EXISTS selecao_pesagens_diarias;
DROP TABLE IF EXISTS selecao_presenca_diaria;
DROP TABLE IF EXISTS selecao_excecoes_calendario;
DROP TABLE IF EXISTS selecao_parametros;
DROP TABLE IF EXISTS selecao_metas_nivel;
ALTER TABLE pessoas
  DROP COLUMN IF EXISTS vinculo,
  DROP COLUMN IF EXISTS nivel_classificacao,
  DROP COLUMN IF EXISTS status_ativa;
COMMIT;
*/
