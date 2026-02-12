-- ===========================================
-- BPA Online - Script de Inicialização PostgreSQL
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
    telefone VARCHAR(20),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- TABELAS BPA INDIVIDUALIZADO
-- ===========================================

CREATE TABLE IF NOT EXISTS bpa_individualizado (
    id SERIAL PRIMARY KEY,
    cnes VARCHAR(7) NOT NULL,
    competencia VARCHAR(6) NOT NULL,
    folha INTEGER DEFAULT 1,
    sequencia INTEGER DEFAULT 1,
    
    -- Profissional
    cns_profissional VARCHAR(15) NOT NULL,
    cbo VARCHAR(6) NOT NULL,
    ine VARCHAR(10),
    
    -- Paciente
    cns_paciente VARCHAR(15) NOT NULL,
    cpf_paciente VARCHAR(11),
    nome_paciente VARCHAR(255) NOT NULL,
    data_nascimento VARCHAR(8) NOT NULL,
    sexo VARCHAR(1) NOT NULL,
    raca_cor VARCHAR(2) DEFAULT '99',
    nacionalidade VARCHAR(3) DEFAULT '010',
    municipio_ibge VARCHAR(6) NOT NULL,
    
    -- Endereço
    cep VARCHAR(8),
    logradouro_codigo VARCHAR(10),
    endereco VARCHAR(255),
    numero VARCHAR(10),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    telefone VARCHAR(20),
    email VARCHAR(255),
    
    -- Atendimento
    data_atendimento VARCHAR(8) NOT NULL,
    procedimento VARCHAR(10) NOT NULL,
    quantidade INTEGER DEFAULT 1,
    cid VARCHAR(10),
    carater_atendimento VARCHAR(2) DEFAULT '01',
    numero_autorizacao VARCHAR(20),
    cnpj VARCHAR(14),
    servico VARCHAR(3),
    classificacao VARCHAR(3),
    
    -- Controle
    origem VARCHAR(10) DEFAULT 'BPI',
    exportado BOOLEAN DEFAULT FALSE,
    data_exportacao TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para BPA-I
CREATE INDEX IF NOT EXISTS idx_bpai_cnes ON bpa_individualizado(cnes);
CREATE INDEX IF NOT EXISTS idx_bpai_competencia ON bpa_individualizado(competencia);
CREATE INDEX IF NOT EXISTS idx_bpai_cnes_comp ON bpa_individualizado(cnes, competencia);
CREATE INDEX IF NOT EXISTS idx_bpai_exportado ON bpa_individualizado(exportado);
CREATE INDEX IF NOT EXISTS idx_bpai_cns_pac ON bpa_individualizado(cns_paciente);

-- ===========================================
-- TABELAS BPA CONSOLIDADO
-- ===========================================

CREATE TABLE IF NOT EXISTS bpa_consolidado (
    id SERIAL PRIMARY KEY,
    cnes VARCHAR(7) NOT NULL,
    competencia VARCHAR(6) NOT NULL,
    folha INTEGER DEFAULT 1,
    
    -- Profissional
    cns_profissional VARCHAR(15) NOT NULL,
    cbo VARCHAR(6) NOT NULL,
    
    -- Procedimento
    procedimento VARCHAR(10) NOT NULL,
    quantidade INTEGER DEFAULT 1,
    idade VARCHAR(3),
    
    -- Controle
    origem VARCHAR(10) DEFAULT 'BPC',
    exportado BOOLEAN DEFAULT FALSE,
    data_exportacao TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para BPA-C
CREATE INDEX IF NOT EXISTS idx_bpac_cnes ON bpa_consolidado(cnes);
CREATE INDEX IF NOT EXISTS idx_bpac_competencia ON bpa_consolidado(competencia);
CREATE INDEX IF NOT EXISTS idx_bpac_cnes_comp ON bpa_consolidado(cnes, competencia);
CREATE INDEX IF NOT EXISTS idx_bpac_exportado ON bpa_consolidado(exportado);

-- ===========================================
-- TABELAS DE EXPORTAÇÃO
-- ===========================================

CREATE TABLE IF NOT EXISTS exportacoes (
    id SERIAL PRIMARY KEY,
    cnes VARCHAR(7) NOT NULL,
    competencia VARCHAR(6) NOT NULL,
    tipo VARCHAR(10) NOT NULL, -- 'BPA-I', 'BPA-C', 'AMBOS'
    arquivo VARCHAR(255),
    total_registros INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pendente', -- 'pendente', 'processando', 'concluido', 'erro'
    erro TEXT,
    usuario_id INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- TABELAS DE PROCEDIMENTOS E REFERÊNCIAS
-- ===========================================

CREATE TABLE IF NOT EXISTS procedimentos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    descricao VARCHAR(255),
    tipo VARCHAR(10), -- 'BPA-I', 'BPA-C', 'AMBOS'
    valor DECIMAL(10,2),
    ativo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS cbo (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(6) UNIQUE NOT NULL,
    descricao VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS cid (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    descricao VARCHAR(255)
);

-- ===========================================
-- TABELA DE LOG DE OPERAÇÕES
-- ===========================================

CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    acao VARCHAR(100) NOT NULL,
    tabela VARCHAR(50),
    registro_id INTEGER,
    dados_anteriores JSONB,
    dados_novos JSONB,
    ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- USUÁRIO ADMIN PADRÃO
-- ===========================================

INSERT INTO usuarios (username, nome, email, password_hash, perfil, ativo)
VALUES ('admin', 'Administrador', 'admin@bpaonline.local', 
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VDdp.8UZrA7f/m', -- senha: admin123
        'admin', TRUE)
ON CONFLICT (username) DO NOTHING;

-- ===========================================
-- FUNÇÕES AUXILIARES
-- ===========================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
DROP TRIGGER IF EXISTS update_usuarios_updated_at ON usuarios;
CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_profissionais_updated_at ON profissionais;
CREATE TRIGGER update_profissionais_updated_at BEFORE UPDATE ON profissionais
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pacientes_updated_at ON pacientes;
CREATE TRIGGER update_pacientes_updated_at BEFORE UPDATE ON pacientes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_bpai_updated_at ON bpa_individualizado;
CREATE TRIGGER update_bpai_updated_at BEFORE UPDATE ON bpa_individualizado
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_bpac_updated_at ON bpa_consolidado;
CREATE TRIGGER update_bpac_updated_at BEFORE UPDATE ON bpa_consolidado
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Mensagem de confirmação
DO $$
BEGIN
    RAISE NOTICE 'BPA Online - Banco de dados inicializado com sucesso!';
END $$;
