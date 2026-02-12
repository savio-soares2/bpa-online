-- Tabelas SIGTAP para filtragem dinâmica de procedimentos

-- Tabela de procedimentos
CREATE TABLE IF NOT EXISTS sigtap_procedimento (
    co_procedimento VARCHAR(10) PRIMARY KEY,
    no_procedimento VARCHAR(250) NOT NULL,
    tp_complexidade CHAR(1),
    tp_sexo CHAR(1),
    qt_maxima_execucao INT,
    qt_dias_permanencia INT,
    qt_pontos INT,
    vl_idade_minima INT,
    vl_idade_maxima INT,
    vl_sh DECIMAL(15,2),
    vl_sa DECIMAL(15,2),
    vl_sp DECIMAL(15,2),
    co_financiamento VARCHAR(2),
    co_rubrica VARCHAR(6),
    qt_tempo_permanencia INT,
    dt_competencia CHAR(6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de ocupações (CBO)
CREATE TABLE IF NOT EXISTS sigtap_ocupacao (
    co_ocupacao VARCHAR(6) PRIMARY KEY,
    no_ocupacao VARCHAR(150) NOT NULL,
    dt_competencia CHAR(6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de serviços/classificações
CREATE TABLE IF NOT EXISTS sigtap_servico (
    co_servico VARCHAR(3) NOT NULL,
    co_classificacao VARCHAR(3) NOT NULL,
    no_servico_classificacao VARCHAR(200) NOT NULL,
    dt_competencia CHAR(6),
    PRIMARY KEY (co_servico, co_classificacao),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de instrumentos de registro (BPA-C, BPA-I, etc)
CREATE TABLE IF NOT EXISTS sigtap_registro (
    co_registro VARCHAR(2) PRIMARY KEY,
    no_registro VARCHAR(50) NOT NULL,
    dt_competencia CHAR(6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação procedimento x CBO (quais CBOs podem executar quais procedimentos)
CREATE TABLE IF NOT EXISTS sigtap_proc_cbo (
    co_procedimento VARCHAR(10) NOT NULL,
    co_ocupacao VARCHAR(6) NOT NULL,
    dt_competencia CHAR(6),
    PRIMARY KEY (co_procedimento, co_ocupacao),
    FOREIGN KEY (co_procedimento) REFERENCES sigtap_procedimento(co_procedimento),
    FOREIGN KEY (co_ocupacao) REFERENCES sigtap_ocupacao(co_ocupacao),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação procedimento x serviço (quais tipos de estabelecimento podem executar quais procedimentos)
CREATE TABLE IF NOT EXISTS sigtap_proc_servico (
    co_procedimento VARCHAR(10) NOT NULL,
    co_servico VARCHAR(3) NOT NULL,
    co_classificacao VARCHAR(3) NOT NULL,
    dt_competencia CHAR(6),
    PRIMARY KEY (co_procedimento, co_servico, co_classificacao),
    FOREIGN KEY (co_procedimento) REFERENCES sigtap_procedimento(co_procedimento),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação procedimento x instrumento de registro (BPA-C, BPA-I, AIH, APAC, etc)
CREATE TABLE IF NOT EXISTS sigtap_proc_registro (
    co_procedimento VARCHAR(10) NOT NULL,
    co_registro VARCHAR(2) NOT NULL,
    dt_competencia CHAR(6),
    PRIMARY KEY (co_procedimento, co_registro),
    FOREIGN KEY (co_procedimento) REFERENCES sigtap_procedimento(co_procedimento),
    FOREIGN KEY (co_registro) REFERENCES sigtap_registro(co_registro),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimizar consultas
CREATE INDEX IF NOT EXISTS idx_proc_cbo_ocupacao ON sigtap_proc_cbo(co_ocupacao);
CREATE INDEX IF NOT EXISTS idx_proc_servico_servico ON sigtap_proc_servico(co_servico, co_classificacao);
CREATE INDEX IF NOT EXISTS idx_proc_registro_registro ON sigtap_proc_registro(co_registro);
CREATE INDEX IF NOT EXISTS idx_procedimento_nome ON sigtap_procedimento(no_procedimento);

-- Comentários para documentação
COMMENT ON TABLE sigtap_procedimento IS 'Tabela de procedimentos do SIGTAP/DATASUS';
COMMENT ON TABLE sigtap_ocupacao IS 'Tabela de ocupações (CBO) do SIGTAP';
COMMENT ON TABLE sigtap_servico IS 'Tabela de serviços/classificações de estabelecimento do SIGTAP';
COMMENT ON TABLE sigtap_registro IS 'Instrumentos de registro (BPA-C=01, BPA-I=02, AIH=03, etc)';
COMMENT ON TABLE sigtap_proc_cbo IS 'Relação de quais CBOs podem executar cada procedimento';
COMMENT ON TABLE sigtap_proc_servico IS 'Relação de quais tipos de estabelecimento podem executar cada procedimento';
COMMENT ON TABLE sigtap_proc_registro IS 'Relação de em quais instrumentos cada procedimento pode ser registrado';
