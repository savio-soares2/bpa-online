-- ===========================================
-- BPA Online - Script de Inicialização PostgreSQL
-- Nomes de colunas compatíveis com Firebird S_PRD (PRD_*)
-- ===========================================

-- Extensão para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- TABELAS DE AUTENTICAÇÃO
-- ===========================================

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    cnes VARCHAR(7),
    nome_unidade VARCHAR(255),
    perfil VARCHAR(50) DEFAULT 'digitador',
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- TABELAS DE PROFISSIONAIS E PACIENTES
-- ===========================================

CREATE TABLE IF NOT EXISTS profissionais (
    id SERIAL PRIMARY KEY,
    cnes VARCHAR(7) NOT NULL,
    cns VARCHAR(15) NOT NULL,
    cpf VARCHAR(11),
    nome VARCHAR(255) NOT NULL,
    cbo VARCHAR(6) NOT NULL,
    ine VARCHAR(10),
    vinculo VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cnes, cns)
);

CREATE TABLE IF NOT EXISTS pacientes (
    id SERIAL PRIMARY KEY,
    cns VARCHAR(15) UNIQUE NOT NULL,
    cpf VARCHAR(11),
    nome VARCHAR(255) NOT NULL,
    data_nascimento VARCHAR(8),
    sexo VARCHAR(1),
    raca_cor VARCHAR(2),
    nacionalidade VARCHAR(3) DEFAULT '010',
    municipio_ibge VARCHAR(6),
    cep VARCHAR(8),
    logradouro_codigo VARCHAR(10),
    endereco VARCHAR(255),
    numero VARCHAR(10),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    telefone VARCHAR(50),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- TABELA BPA INDIVIDUALIZADO (PRD_* - Firebird)
-- ===========================================

CREATE TABLE IF NOT EXISTS bpa_individualizado (
    id SERIAL PRIMARY KEY,
    
    -- Identificação (PRD_*)
    prd_uid VARCHAR(7),           -- CNES
    prd_cmp VARCHAR(6),           -- Competência
    prd_flh INTEGER DEFAULT 1,    -- Folha (sempre 1)
    prd_seq INTEGER DEFAULT 1,    -- Sequência
    
    -- Profissional
    prd_cnsmed VARCHAR(15),       -- CNS Profissional
    prd_cbo VARCHAR(6),           -- CBO
    prd_ine VARCHAR(10),          -- INE (vazio)
    
    -- Paciente
    prd_cnspac VARCHAR(15),       -- CNS Paciente
    prd_cpf_pcnte VARCHAR(11),    -- CPF Paciente
    prd_nmpac VARCHAR(255),       -- Nome Paciente
    prd_dtnasc VARCHAR(8),        -- Data Nascimento
    prd_sexo VARCHAR(1),          -- Sexo
    prd_raca VARCHAR(2) DEFAULT '99',          -- Raça/Cor
    prd_nac VARCHAR(3) DEFAULT '010',          -- Nacionalidade
    prd_ibge VARCHAR(6),          -- Município IBGE
    prd_idade VARCHAR(3),         -- Idade
    
    -- Endereço do Paciente
    prd_cep_pcnte VARCHAR(8),     -- CEP
    prd_lograd_pcnte VARCHAR(10), -- Código Logradouro
    prd_end_pcnte VARCHAR(255),   -- Endereço
    prd_num_pcnte VARCHAR(10),    -- Número
    prd_compl_pcnte VARCHAR(100), -- Complemento
    prd_bairro_pcnte VARCHAR(100),-- Bairro
    prd_ddtel_pcnte VARCHAR(2),   -- DDD Telefone
    prd_tel_pcnte VARCHAR(50),    -- Telefone
    prd_email_pcnte VARCHAR(255), -- Email
    
    -- Atendimento
    prd_dtaten VARCHAR(8),        -- Data Atendimento
    prd_pa VARCHAR(10),           -- Procedimento
    prd_qt_p INTEGER DEFAULT 1,   -- Quantidade
    prd_cid VARCHAR(10),          -- CID
    prd_caten VARCHAR(2) DEFAULT '01',         -- Caráter Atendimento
    prd_naut VARCHAR(50),         -- Número Autorização
    prd_cnpj VARCHAR(14),         -- CNPJ
    prd_servico VARCHAR(3),       -- Serviço
    prd_classificacao VARCHAR(3), -- Classificação
    prd_etnia VARCHAR(4),         -- Etnia
    prd_eqp_area VARCHAR(10),     -- Equipe Área
    prd_eqp_seq VARCHAR(10),      -- Equipe Sequência
    
    -- Campos Firebird adicionais
    prd_mvm VARCHAR(6),           -- Movimento (= competência)
    prd_advqt VARCHAR(2) DEFAULT '00',         -- ADV Quantidade
    prd_flpa VARCHAR(1) DEFAULT '0',           -- Flag PA
    prd_flcbo VARCHAR(1) DEFAULT '0',          -- Flag CBO
    prd_flca VARCHAR(1) DEFAULT '0',           -- Flag CA
    prd_flida VARCHAR(1) DEFAULT '0',          -- Flag Idade
    prd_flqt VARCHAR(1) DEFAULT '0',           -- Flag Quantidade
    prd_fler VARCHAR(1) DEFAULT '0',           -- Flag Erro
    prd_flmun VARCHAR(1) DEFAULT '0',          -- Flag Município
    prd_flcid VARCHAR(1) DEFAULT '0',          -- Flag CID
    
    -- Controle
    prd_org VARCHAR(10) DEFAULT 'BPI',         -- Origem (BPI, JULIA, etc)
    prd_exportado BOOLEAN DEFAULT FALSE,       -- Exportado
    data_exportacao TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para BPA-I
CREATE INDEX IF NOT EXISTS idx_bpai_uid ON bpa_individualizado(prd_uid);
CREATE INDEX IF NOT EXISTS idx_bpai_cmp ON bpa_individualizado(prd_cmp);
CREATE INDEX IF NOT EXISTS idx_bpai_uid_cmp ON bpa_individualizado(prd_uid, prd_cmp);
CREATE INDEX IF NOT EXISTS idx_bpai_exportado ON bpa_individualizado(prd_exportado);
CREATE INDEX IF NOT EXISTS idx_bpai_cnspac ON bpa_individualizado(prd_cnspac);

-- ===========================================
-- TABELA BPA CONSOLIDADO (PRD_* - Firebird)
-- ===========================================

CREATE TABLE IF NOT EXISTS bpa_consolidado (
    id SERIAL PRIMARY KEY,
    
    -- Identificação
    prd_uid VARCHAR(7),           -- CNES
    prd_cmp VARCHAR(6),           -- Competência
    prd_flh INTEGER DEFAULT 1,    -- Folha
    
    -- Profissional
    prd_cnsmed VARCHAR(15),       -- CNS Profissional
    prd_cbo VARCHAR(6),           -- CBO
    
    -- Procedimento
    prd_pa VARCHAR(10),           -- Procedimento
    prd_qt_p INTEGER DEFAULT 1,   -- Quantidade
    prd_idade VARCHAR(3),         -- Idade
    
    -- Controle
    prd_org VARCHAR(10) DEFAULT 'BPC',
    prd_exportado BOOLEAN DEFAULT FALSE,
    data_exportacao TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para BPA-C
CREATE INDEX IF NOT EXISTS idx_bpac_uid ON bpa_consolidado(prd_uid);
CREATE INDEX IF NOT EXISTS idx_bpac_cmp ON bpa_consolidado(prd_cmp);
CREATE INDEX IF NOT EXISTS idx_bpac_exportado ON bpa_consolidado(prd_exportado);

-- ===========================================
-- TABELA DE EXPORTAÇÕES
-- ===========================================

CREATE TABLE IF NOT EXISTS exportacoes (
    id SERIAL PRIMARY KEY,
    cnes VARCHAR(7) NOT NULL,
    competencia VARCHAR(6) NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    arquivo VARCHAR(255),
    total_registros INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pendente',
    erro TEXT,
    usuario_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- TABELA DE HISTÓRICO DE EXTRAÇÕES
-- ===========================================

CREATE TABLE IF NOT EXISTS historico_extracoes (
    id SERIAL PRIMARY KEY,
    cnes VARCHAR(7) NOT NULL,
    competencia VARCHAR(6) NOT NULL,
    
    -- Totais extraídos
    total_bpa_i INTEGER DEFAULT 0,
    total_bpa_c INTEGER DEFAULT 0,
    total_removido INTEGER DEFAULT 0,
    total_geral INTEGER DEFAULT 0,
    
    -- Valores financeiros
    valor_total_bpa_i DECIMAL(12,2) DEFAULT 0.00,
    valor_total_bpa_c DECIMAL(12,2) DEFAULT 0.00,
    valor_total_geral DECIMAL(12,2) DEFAULT 0.00,
    
    -- Estatísticas (JSON)
    procedimentos_mais_usados JSONB,  -- [{codigo, nome, quantidade, valor_total}]
    profissionais_mais_ativos JSONB,  -- [{cns, cbo, quantidade}]
    distribuicao_por_dia JSONB,       -- {dia: quantidade}
    
    -- Metadados
    usuario_id INTEGER,
    duracao_segundos INTEGER,
    status VARCHAR(20) DEFAULT 'concluido',
    erro TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE INDEX IF NOT EXISTS idx_historico_cnes ON historico_extracoes(cnes);
CREATE INDEX IF NOT EXISTS idx_historico_competencia ON historico_extracoes(competencia);
CREATE INDEX IF NOT EXISTS idx_historico_created_at ON historico_extracoes(created_at DESC);

-- ===========================================
-- USUÁRIO ADMIN PADRÃO
-- ===========================================

-- Senha: admin123 (bcrypt hash)
INSERT INTO usuarios (username, nome, email, password_hash, cnes, nome_unidade, perfil, ativo)
VALUES (
    'admin',
    'Administrador',
    'admin@sms.recife.pe.gov.br',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpNDO.3eSqbFfC',
    '6061478',
    'CAPS AD III DAVID CAPISTRANO',
    'admin',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- ===========================================
-- COMENTÁRIOS
-- ===========================================

COMMENT ON TABLE bpa_individualizado IS 'BPA Individualizado - Nomes compatíveis com Firebird S_PRD';
COMMENT ON COLUMN bpa_individualizado.prd_uid IS 'CNES do estabelecimento';
COMMENT ON COLUMN bpa_individualizado.prd_cmp IS 'Competência AAAAMM';
COMMENT ON COLUMN bpa_individualizado.prd_flh IS 'Número da folha (sempre 1)';
COMMENT ON COLUMN bpa_individualizado.prd_seq IS 'Sequência na folha';
COMMENT ON COLUMN bpa_individualizado.prd_cnsmed IS 'CNS do profissional';
COMMENT ON COLUMN bpa_individualizado.prd_cnspac IS 'CNS do paciente';
COMMENT ON COLUMN bpa_individualizado.prd_caten IS 'Caráter atendimento: 01=Eletivo, 02=Urgência';
COMMENT ON COLUMN bpa_individualizado.prd_mvm IS 'Movimento (= competência)';
