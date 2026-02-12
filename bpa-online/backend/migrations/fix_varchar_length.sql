-- ===========================================
-- FIX: Aumentar tamanho de campos VARCHAR(20) 
-- para evitar perda de dados
-- ===========================================

-- Tabela pacientes - aumentar telefone
ALTER TABLE pacientes 
ALTER COLUMN telefone TYPE VARCHAR(50);

-- Tabela bpa_individualizado - aumentar telefone e número autorização
ALTER TABLE bpa_individualizado 
ALTER COLUMN prd_tel_pcnte TYPE VARCHAR(50);

ALTER TABLE bpa_individualizado 
ALTER COLUMN prd_naut TYPE VARCHAR(50);

-- Verificar mudanças
SELECT 
    table_name, 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns
WHERE table_name IN ('pacientes', 'bpa_individualizado')
  AND column_name IN ('telefone', 'prd_tel_pcnte', 'prd_naut')
ORDER BY table_name, column_name;
