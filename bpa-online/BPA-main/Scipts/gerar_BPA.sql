select tb_unidade_saude.nu_cnes as PRD_UID,
       cast(extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) as varchar(6)) AS PRD_CMP,
       tb_prof.nu_cns AS PRD_CNSMED,
       tb_cbo.co_cbo_2002 AS PRD_CBO,
       '1' AS PRD_FLH,
       '1' AS PRD_SEQ,

        case
           when tb_proced.co_proced like 'A%' then SUBSTRING(tb_proced.co_proced_filtro, 9,10)
           else tb_proced.co_proced
        end as prd_pa,

  --     tb_proced.co_proced ,
  --    tb_proced.no_proced,
       tb_cidadao.nu_cns AS PRD_CNSPAC,
       SUBSTRING(tb_cidadao.no_cidadao, 1,30) AS PRD_NMPAC,
       extract(YEAR FROM tb_cidadao.dt_nascimento)||CAST(LPAD(cast(extract(MONTH FROM tb_cidadao.dt_nascimento) as varchar(2)),2,'0') AS VARCHAR(2))||CAST(LPAD(cast(extract(DAY FROM tb_cidadao.dt_nascimento) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_DTNASC,
       CASE
         WHEN tb_cidadao.no_sexo = 'FEMININO' THEN 'F'
         ELSE 'M'
       END AS PRD_SEXO,
       SUBSTRING(tb_localidade.co_ibge,1,6) AS PRD_IBGE,
       extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2))||CAST(LPAD(cast(extract(DAY FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_DTATEN,
       TB_CID10.nu_cid10 AS PRD_CID,
       CAST(LPAD(cast(extract(year from age(tb_cidadao.dt_nascimento)) as varchar(3)),3,'0') AS VARCHAR(3)) AS PRD_IDADE,
       1 AS PRD_QT_P,
       CASE
         WHEN tb_unidade_saude.nu_cnes IN ('2755289','2492555','2829606') THEN '02'
         ELSE '01'
       END AS PRD_CATEN,
       '' AS PRD_NAUT,
       'BPI' AS PRD_ORG,
       extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_MVM,
       '0' AS PRD_FLPA,
       '0' AS PRD_FLCBO,
       '0' AS PRD_FLCA,
       '0' AS PRD_FLIDA,
       '0' AS PRD_FLQT,
       '0' AS PRD_FLER,
       '0' AS PRD_FLMUN,
       '0' AS PRD_FLCID,
       CAST(LPAD(cast(tb_cidadao.co_raca_cor as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_RACA,
       '' AS PRD_SERVICO,
       '' AS PRD_CLASSIFICACAO,
       '' AS PRD_ETNIA,
       '010' AS PRD_NAC,
       '00' AS PRD_ADVQT,
       '' AS PRD_CNPJ,
       '' AS PRD_EQP_AREA,
       '' AS PRD_EQP_SEQ,
       tb_tipo_logradouro.nu_dne  AS PRD_LOGRAD_PCNTE,
       tb_cidadao.ds_cep AS PRD_CEP_PCNTE,
       SUBSTRING(tb_cidadao.ds_logradouro,1,30) AS PRD_END_PCNTE,
       SUBSTRING(tb_cidadao.ds_complemento,1,10) AS PRD_COMPL_PCNTE,
       SUBSTRING(tb_cidadao.nu_numero,1,5) AS PRD_NUM_PCNTE,
       SUBSTRING(tb_cidadao.no_bairro,1,30) AS PRD_BAIRRO_PCNTE,
       substring(tb_cidadao.nu_telefone_residencial, 1 , 2) AS PRD_DDTEL_PCNTE,
       substring(tb_cidadao.nu_telefone_residencial, 3 , 9) AS PRD_TEL_PCNTE,
       '' AS PRD_EMAIL_PCNTE,
       '' AS PRD_INE

from public.tb_atend
left join public.tb_status_atend on tb_status_atend.co_status_atend = tb_atend.st_atend
left join public.tb_unidade_saude on tb_unidade_saude.co_seq_unidade_saude = tb_atend.co_unidade_saude

LEFT JOIN public.tb_atend_prof ON tb_atend_prof.co_atend = tb_atend.co_seq_atend

left join public.tb_lotacao on tb_lotacao.co_ator_papel = tb_atend_prof.co_lotacao
left join public.tb_prof on tb_prof.co_seq_prof = tb_lotacao.co_prof
left join public.tb_uf on tb_uf.co_uf = tb_prof.co_uf_emissora_conselho_classe
left join public.tb_conselho_classe on tb_conselho_classe.co_conselho_classe = tb_prof.co_conselho_classe
left join public.tb_cbo on tb_cbo.co_cbo = tb_lotacao.co_cbo

left join public.rl_atend_proced on rl_atend_proced.co_atend_prof = tb_atend_prof.co_seq_atend_prof
inner join public.tb_proced on tb_proced.co_seq_proced = Rl_atend_proced.co_proced

LEFT JOIN public.rl_evolucao_avaliacao_ciap_cid ON rl_evolucao_avaliacao_ciap_cid.co_atend_prof = tb_atend_prof.co_seq_atend_prof
LEFT JOIN public.tb_cid10 ON tb_cid10.co_cid10 = rl_evolucao_avaliacao_ciap_cid.co_cid10

left join public.tb_prontuario on tb_prontuario.co_seq_prontuario = tb_atend.co_prontuario
left join public.tb_cidadao on tb_cidadao.co_seq_cidadao = tb_prontuario.co_cidadao
left join public.tb_tipo_logradouro on tb_tipo_logradouro.co_tipo_logradouro = tb_cidadao.tp_logradouro

left join tb_localidade on tb_localidade.co_localidade = tb_cidadao.co_localidade_endereco
left join tb_uf pes_uf on pes_uf.co_uf = tb_cidadao.co_uf
where tb_unidade_saude.nu_cnes in ('__CNES__')
  and to_char(tb_atend.dt_inicio, 'yyyy-mm') = '__COMPETENCIA__'
  and tb_proced.co_proced not in ('ABPO015','ABPG040','ABPG039','ABPG038','ABPG034','ABEX022','ABEX013','ABEX012')

union all

  select tb_unidade_saude.nu_cnes as PRD_UID,
       cast(extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) as varchar(6)) AS PRD_CMP,
       tb_prof.nu_cns AS PRD_CNSMED,
       tb_cbo.co_cbo_2002 AS PRD_CBO,
       '1' AS PRD_FLH,
       '1' AS PRD_SEQ,
        case
           when tb_proced.co_proced like 'A%' then SUBSTRING(tb_proced.co_proced_filtro, 9,10)
           else tb_proced.co_proced
        end as prd_pa,

   --    tb_proced.co_proced ,
   --    tb_proced.no_proced,
       tb_cidadao.nu_cns AS PRD_CNSPAC,
       SUBSTRING(tb_cidadao.no_cidadao, 1,30) AS PRD_NMPAC,
       extract(YEAR FROM tb_cidadao.dt_nascimento)||CAST(LPAD(cast(extract(MONTH FROM tb_cidadao.dt_nascimento) as varchar(2)),2,'0') AS VARCHAR(2))||CAST(LPAD(cast(extract(DAY FROM tb_cidadao.dt_nascimento) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_DTNASC,
       CASE
         WHEN tb_cidadao.no_sexo = 'FEMININO' THEN 'F'
         ELSE 'M'
       END AS PRD_SEXO,
       SUBSTRING(tb_localidade.co_ibge,1,6) AS PRD_IBGE,
       extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2))||CAST(LPAD(cast(extract(DAY FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_DTATEN,
       TB_CID10.nu_cid10 AS PRD_CID,
       CAST(LPAD(cast(extract(year from age(tb_cidadao.dt_nascimento)) as varchar(3)),3,'0') AS VARCHAR(3)) AS PRD_IDADE,
       1 AS PRD_QT_P,
       CASE
         WHEN tb_unidade_saude.nu_cnes IN ('2755289','2492555','2829606') THEN '02'
         ELSE '01'
       END AS PRD_CATEN,
       '' AS PRD_NAUT,
       'BPI' AS PRD_ORG,
       extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_MVM,
       '0' AS PRD_FLPA,
       '0' AS PRD_FLCBO,
       '0' AS PRD_FLCA,
       '0' AS PRD_FLIDA,
       '0' AS PRD_FLQT,
       '0' AS PRD_FLER,
       '0' AS PRD_FLMUN,
       '0' AS PRD_FLCID,
       CAST(LPAD(cast(tb_cidadao.co_raca_cor as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_RACA,
       '' AS PRD_SERVICO,
       '' AS PRD_CLASSIFICACAO,
       '' AS PRD_ETNIA,
       '010' AS PRD_NAC,
       '00' AS PRD_ADVQT,
       '' AS PRD_CNPJ,
       '' AS PRD_EQP_AREA,
       '' AS PRD_EQP_SEQ,
       tb_tipo_logradouro.nu_dne  AS PRD_LOGRAD_PCNTE,
       tb_cidadao.ds_cep AS PRD_CEP_PCNTE,
       SUBSTRING(tb_cidadao.ds_logradouro,1,30) AS PRD_END_PCNTE,
       SUBSTRING(tb_cidadao.ds_complemento,1,10) AS PRD_COMPL_PCNTE,
       SUBSTRING(tb_cidadao.nu_numero,1,5) AS PRD_NUM_PCNTE,
       SUBSTRING(tb_cidadao.no_bairro,1,30) AS PRD_BAIRRO_PCNTE,
       substring(tb_cidadao.nu_telefone_residencial, 1 , 2) AS PRD_DDTEL_PCNTE,
       substring(tb_cidadao.nu_telefone_residencial, 3 , 9) AS PRD_TEL_PCNTE,
       '' AS PRD_EMAIL_PCNTE,
       '' AS PRD_INE

from public.tb_atend
left join public.tb_status_atend on tb_status_atend.co_status_atend = tb_atend.st_atend
left join public.tb_unidade_saude on tb_unidade_saude.co_seq_unidade_saude = tb_atend.co_unidade_saude

LEFT JOIN public.tb_atend_prof ON tb_atend_prof.co_atend = tb_atend.co_seq_atend

left join public.tb_lotacao on tb_lotacao.co_ator_papel = tb_atend_prof.co_lotacao
left join public.tb_prof on tb_prof.co_seq_prof = tb_lotacao.co_prof
left join public.tb_uf on tb_uf.co_uf = tb_prof.co_uf_emissora_conselho_classe
left join public.tb_conselho_classe on tb_conselho_classe.co_conselho_classe = tb_prof.co_conselho_classe
left join public.tb_cbo on tb_cbo.co_cbo = tb_lotacao.co_cbo

left join rl_evolucao_plano_ciap on rl_evolucao_plano_ciap.co_atend_prof = tb_atend_prof.co_seq_atend_prof
inner join tb_proced on tb_proced.co_seq_proced = rl_evolucao_plano_ciap.co_proced

LEFT JOIN public.rl_evolucao_avaliacao_ciap_cid ON rl_evolucao_avaliacao_ciap_cid.co_atend_prof = tb_atend_prof.co_seq_atend_prof
LEFT JOIN public.tb_cid10 ON tb_cid10.co_cid10 = rl_evolucao_avaliacao_ciap_cid.co_cid10

left join public.tb_prontuario on tb_prontuario.co_seq_prontuario = tb_atend.co_prontuario
left join public.tb_cidadao on tb_cidadao.co_seq_cidadao = tb_prontuario.co_cidadao
left join public.tb_tipo_logradouro on tb_tipo_logradouro.co_tipo_logradouro = tb_cidadao.tp_logradouro

left join tb_localidade on tb_localidade.co_localidade = tb_cidadao.co_localidade_endereco
left join tb_uf pes_uf on pes_uf.co_uf = tb_cidadao.co_uf
where tb_unidade_saude.nu_cnes in ('__CNES__')
  and to_char(tb_atend.dt_inicio, 'yyyy-mm') = '__COMPETENCIA__'
  and tb_proced.co_proced not in ('ABPO015','ABPG040','ABPG039','ABPG038','ABPG034','ABEX022','ABEX013','ABEX012')

union all

  select tb_unidade_saude.nu_cnes as PRD_UID,
       cast(extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) as varchar(6)) AS PRD_CMP,
       tb_prof.nu_cns AS PRD_CNSMED,
       tb_cbo.co_cbo_2002 AS PRD_CBO,
       '1' AS PRD_FLH,
       '1' AS PRD_SEQ,
        case
           when tb_proced.co_proced like 'A%' then SUBSTRING(tb_proced.co_proced_filtro, 9,10)
           else tb_proced.co_proced
        end as prd_pa,

   --    tb_proced.co_proced ,
  --     tb_proced.no_proced,
       tb_cidadao.nu_cns AS PRD_CNSPAC,
       SUBSTRING(tb_cidadao.no_cidadao, 1,30) AS PRD_NMPAC,
       extract(YEAR FROM tb_cidadao.dt_nascimento)||CAST(LPAD(cast(extract(MONTH FROM tb_cidadao.dt_nascimento) as varchar(2)),2,'0') AS VARCHAR(2))||CAST(LPAD(cast(extract(DAY FROM tb_cidadao.dt_nascimento) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_DTNASC,
       CASE
         WHEN tb_cidadao.no_sexo = 'FEMININO' THEN 'F'
         ELSE 'M'
       END AS PRD_SEXO,
       SUBSTRING(tb_localidade.co_ibge,1,6) AS PRD_IBGE,
       extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2))||CAST(LPAD(cast(extract(DAY FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_DTATEN,
       TB_CID10.nu_cid10 AS PRD_CID,
       CAST(LPAD(cast(extract(year from age(tb_cidadao.dt_nascimento)) as varchar(3)),3,'0') AS VARCHAR(3)) AS PRD_IDADE,
       1 AS PRD_QT_P,
       CASE
         WHEN tb_unidade_saude.nu_cnes IN ('2755289','2492555','2829606') THEN '02'
         ELSE '01'
       END AS PRD_CATEN,
       '' AS PRD_NAUT,
       'BPI' AS PRD_ORG,
       extract(YEAR FROM tb_atend.dt_inicio)||CAST(LPAD(cast(extract(MONTH FROM tb_atend.dt_inicio) as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_MVM,
       '0' AS PRD_FLPA,
       '0' AS PRD_FLCBO,
       '0' AS PRD_FLCA,
       '0' AS PRD_FLIDA,
       '0' AS PRD_FLQT,
       '0' AS PRD_FLER,
       '0' AS PRD_FLMUN,
       '0' AS PRD_FLCID,
       CAST(LPAD(cast(tb_cidadao.co_raca_cor as varchar(2)),2,'0') AS VARCHAR(2)) AS PRD_RACA,
       '' AS PRD_SERVICO,
       '' AS PRD_CLASSIFICACAO,
       '' AS PRD_ETNIA,
       '010' AS PRD_NAC,
       '00' AS PRD_ADVQT,
       '' AS PRD_CNPJ,
       '' AS PRD_EQP_AREA,
       '' AS PRD_EQP_SEQ,
       tb_tipo_logradouro.nu_dne  AS PRD_LOGRAD_PCNTE,
       tb_cidadao.ds_cep AS PRD_CEP_PCNTE,
       SUBSTRING(tb_cidadao.ds_logradouro,1,30) AS PRD_END_PCNTE,
       SUBSTRING(tb_cidadao.ds_complemento,1,10) AS PRD_COMPL_PCNTE,
       SUBSTRING(tb_cidadao.nu_numero,1,5) AS PRD_NUM_PCNTE,
       SUBSTRING(tb_cidadao.no_bairro,1,30) AS PRD_BAIRRO_PCNTE,
       substring(tb_cidadao.nu_telefone_residencial, 1 , 2) AS PRD_DDTEL_PCNTE,
       substring(tb_cidadao.nu_telefone_residencial, 3 , 9) AS PRD_TEL_PCNTE,
       '' AS PRD_EMAIL_PCNTE,
       '' AS PRD_INE

from public.tb_atend
left join public.tb_status_atend on tb_status_atend.co_status_atend = tb_atend.st_atend
left join public.tb_unidade_saude on tb_unidade_saude.co_seq_unidade_saude = tb_atend.co_unidade_saude

LEFT JOIN public.tb_atend_prof ON tb_atend_prof.co_atend = tb_atend.co_seq_atend

left join public.tb_lotacao on tb_lotacao.co_ator_papel = tb_atend_prof.co_lotacao
left join public.tb_prof on tb_prof.co_seq_prof = tb_lotacao.co_prof
left join public.tb_uf on tb_uf.co_uf = tb_prof.co_uf_emissora_conselho_classe
left join public.tb_conselho_classe on tb_conselho_classe.co_conselho_classe = tb_prof.co_conselho_classe
left join public.tb_cbo on tb_cbo.co_cbo = tb_lotacao.co_cbo

LEFT JOIN public.tb_atend_prof_odonto ON tb_atend_prof_odonto.co_atend_prof_odonto = tb_atend_prof.co_seq_atend_prof
LEFT JOIN public.tb_evolucao_odonto ON tb_evolucao_odonto.co_atend_prof_odonto = tb_atend_prof_odonto.co_atend_prof_odonto

left join rl_evolucao_odonto_proced on rl_evolucao_odonto_proced.co_evolucao_odonto = tb_evolucao_odonto.co_seq_evolucao_odonto
inner join tb_proced on tb_proced.co_seq_proced = rl_evolucao_odonto_proced.co_proced

LEFT JOIN public.rl_evolucao_avaliacao_ciap_cid ON rl_evolucao_avaliacao_ciap_cid.co_atend_prof = tb_atend_prof.co_seq_atend_prof
LEFT JOIN public.tb_cid10 ON tb_cid10.co_cid10 = rl_evolucao_avaliacao_ciap_cid.co_cid10

left join public.tb_prontuario on tb_prontuario.co_seq_prontuario = tb_atend.co_prontuario
left join public.tb_cidadao on tb_cidadao.co_seq_cidadao = tb_prontuario.co_cidadao
left join public.tb_tipo_logradouro on tb_tipo_logradouro.co_tipo_logradouro = tb_cidadao.tp_logradouro

left join tb_localidade on tb_localidade.co_localidade = tb_cidadao.co_localidade_endereco
left join tb_uf pes_uf on pes_uf.co_uf = tb_cidadao.co_uf
where tb_unidade_saude.nu_cnes in ('__CNES__')
  and to_char(tb_atend.dt_inicio, 'yyyy-mm') = '__COMPETENCIA__'
  and tb_proced.co_proced not in ('ABPO015','ABPG040','ABPG039','ABPG038','ABPG034','ABEX022','ABEX013','ABEX012')