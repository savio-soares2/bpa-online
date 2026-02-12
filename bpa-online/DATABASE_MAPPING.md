# Mapeamento do Banco de Dados PostgreSQL - BPA Online
# Gerado em: 2026-02-11 14:12:00
================================================================================

## Total de Tabelas: 25

## Sumário das Tabelas
----------------------------------------
  - auth_group (0 registros)
  - auth_group_permissions (0 registros)
  - auth_permission (48 registros)
  - bpa_consolidado (10073 registros)
  - bpa_individualizado (9847 registros)
  - cbo (0 registros)
  - cid (0 registros)
  - django_admin_log (0 registros)
  - django_content_type (12 registros)
  - django_migrations (19 registros)
  - django_session (0 registros)
  - exportacoes (0 registros)
  - historico_extracoes (68 registros)
  - logs (0 registros)
  - pacientes (3026 registros)
  - procedimentos (0 registros)
  - profissionais (0 registros)
  - sigtap_ocupacao (0 registros)
  - sigtap_proc_cbo (0 registros)
  - sigtap_proc_registro (0 registros)
  - sigtap_proc_servico (0 registros)
  - sigtap_procedimento (0 registros)
  - sigtap_registro (0 registros)
  - sigtap_servico (0 registros)
  - usuarios (1 registros)

================================================================================
## Detalhamento por Tabela
================================================================================

### Tabela: auth_group
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO                                       
name                           character varying(150) NO                                       

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: name

#### Índices:
  - auth_group_name_a6ea08ec_like
  - auth_group_name_key
  - auth_group_pkey


### Tabela: auth_group_permissions
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             bigint               NO                                       
group_id                       integer              NO                                       
permission_id                  integer              NO                                       

#### Constraints:
  - FOREIGN KEY: permission_id -> auth_permission.id
  - FOREIGN KEY: group_id -> auth_group.id
  - PRIMARY KEY: id
  - UNIQUE: group_id
  - UNIQUE: group_id
  - UNIQUE: permission_id
  - UNIQUE: permission_id

#### Índices:
  - auth_group_permissions_group_id_b120cbf9
  - auth_group_permissions_group_id_permission_id_0cd325b0_uniq
  - auth_group_permissions_permission_id_84c5c92e
  - auth_group_permissions_pkey


### Tabela: auth_permission
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO                                       
name                           character varying(255) NO                                       
content_type_id                integer              NO                                       
codename                       character varying(100) NO                                       

#### Constraints:
  - FOREIGN KEY: content_type_id -> django_content_type.id
  - PRIMARY KEY: id
  - UNIQUE: content_type_id
  - UNIQUE: content_type_id
  - UNIQUE: codename
  - UNIQUE: codename

#### Índices:
  - auth_permission_content_type_id_2f476e4b
  - auth_permission_content_type_id_codename_01ab375a_uniq
  - auth_permission_pkey


### Tabela: bpa_consolidado
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('bpa_consolidado_id_  
prd_uid                        character varying(7) NO                                       
prd_cmp                        character varying(6) NO                                       
prd_flh                        integer              YES        1                             
prd_cnsmed                     character varying(15) NO                                       
prd_cbo                        character varying(6) NO                                       
prd_pa                         character varying(10) NO                                       
prd_qt_p                       integer              YES        1                             
prd_idade                      character varying(3) YES                                      
prd_org                        character varying(10) YES        'BPC'::character varying      
prd_exportado                  boolean              YES        false                         
data_exportacao                timestamp without time zone YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
updated_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - PRIMARY KEY: id

#### Índices:
  - bpa_consolidado_pkey
  - idx_bpac_cmp
  - idx_bpac_cnes
  - idx_bpac_cnes_comp
  - idx_bpac_competencia
  - idx_bpac_exportado
  - idx_bpac_uid


### Tabela: bpa_individualizado
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('bpa_individualizado  
prd_uid                        character varying(7) YES                                      
prd_cmp                        character varying(6) YES                                      
prd_flh                        integer              YES        1                             
prd_seq                        integer              YES        1                             
prd_cnsmed                     character varying(15) YES                                      
prd_cbo                        character varying(6) YES                                      
prd_ine                        character varying(10) YES                                      
prd_cnspac                     character varying(15) YES                                      
prd_cpf_pcnte                  character varying(11) YES                                      
prd_nmpac                      character varying(255) YES                                      
prd_dtnasc                     character varying(8) YES                                      
prd_sexo                       character varying(1) YES                                      
prd_raca                       character varying(2) YES        '99'::character varying       
prd_nac                        character varying(3) YES        '010'::character varying      
prd_ibge                       character varying(6) YES                                      
prd_cep_pcnte                  character varying(8) YES                                      
prd_lograd_pcnte               character varying(10) YES                                      
prd_end_pcnte                  character varying(255) YES                                      
prd_num_pcnte                  character varying(10) YES                                      
prd_compl_pcnte                character varying(100) YES                                      
prd_bairro_pcnte               character varying(100) YES                                      
prd_tel_pcnte                  character varying(50) YES                                      
prd_email_pcnte                character varying(255) YES                                      
prd_dtaten                     character varying(8) YES                                      
prd_pa                         character varying(10) YES                                      
prd_qt_p                       integer              YES        1                             
prd_cid                        character varying(10) YES                                      
prd_caten                      character varying(2) YES        '01'::character varying       
prd_naut                       character varying(50) YES                                      
prd_cnpj                       character varying(14) YES                                      
prd_servico                    character varying(3) YES                                      
prd_classificacao              character varying(3) YES                                      
prd_org                        character varying(10) YES        'BPI'::character varying      
prd_exportado                  boolean              YES        false                         
data_exportacao                timestamp without time zone YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
updated_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
prd_idade                      character varying(3) YES                                      
prd_ddtel_pcnte                character varying(2) YES                                      
movimento                      character varying(6) YES                                      
prd_etnia                      character varying(4) YES                                      
prd_eqp_area                   character varying(10) YES                                      
prd_eqp_seq                    character varying(10) YES                                      
advqt                          character varying(2) YES        '00'::character varying       
fl_pa                          character varying(1) YES        '0'::character varying        
fl_cbo                         character varying(1) YES        '0'::character varying        
fl_ca                          character varying(1) YES        '0'::character varying        
fl_ida                         character varying(1) YES        '0'::character varying        
fl_qt                          character varying(1) YES        '0'::character varying        
fl_er                          character varying(1) YES        '0'::character varying        
fl_mun                         character varying(1) YES        '0'::character varying        
fl_cid                         character varying(1) YES        '0'::character varying        
prd_mvm                        character varying(6) YES                                      
prd_advqt                      character varying(2) YES        '00'::character varying       
prd_flpa                       character varying(1) YES        '0'::character varying        
prd_flcbo                      character varying(1) YES        '0'::character varying        
prd_flca                       character varying(1) YES        '0'::character varying        
prd_flida                      character varying(1) YES        '0'::character varying        
prd_flqt                       character varying(1) YES        '0'::character varying        
prd_fler                       character varying(1) YES        '0'::character varying        
prd_flmun                      character varying(1) YES        '0'::character varying        
prd_flcid                      character varying(1) YES        '0'::character varying        

#### Constraints:
  - PRIMARY KEY: id

#### Índices:
  - bpa_individualizado_pkey
  - idx_bpai_cmp
  - idx_bpai_cnes
  - idx_bpai_cnes_comp
  - idx_bpai_cns_pac
  - idx_bpai_cnspac
  - idx_bpai_competencia
  - idx_bpai_exportado
  - idx_bpai_uid
  - idx_bpai_uid_cmp


### Tabela: cbo
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('cbo_id_seq'::regcla  
codigo                         character varying(6) NO                                       
descricao                      character varying(255) YES                                      

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: codigo

#### Índices:
  - cbo_codigo_key
  - cbo_pkey


### Tabela: cid
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('cid_id_seq'::regcla  
codigo                         character varying(10) NO                                       
descricao                      character varying(255) YES                                      

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: codigo

#### Índices:
  - cid_codigo_key
  - cid_pkey


### Tabela: django_admin_log
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO                                       
action_time                    timestamp with time zone NO                                       
object_id                      text                 YES                                      
object_repr                    character varying(200) NO                                       
action_flag                    smallint             NO                                       
change_message                 text                 NO                                       
content_type_id                integer              YES                                      
user_id                        bigint               NO                                       

#### Constraints:
  - FOREIGN KEY: content_type_id -> django_content_type.id
  - FOREIGN KEY: user_id -> usuarios.id
  - PRIMARY KEY: id

#### Índices:
  - django_admin_log_content_type_id_c4bce8eb
  - django_admin_log_pkey
  - django_admin_log_user_id_c564eba6


### Tabela: django_content_type
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO                                       
app_label                      character varying(100) NO                                       
model                          character varying(100) NO                                       

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: model
  - UNIQUE: app_label
  - UNIQUE: app_label
  - UNIQUE: model

#### Índices:
  - django_content_type_app_label_model_76bd3d3b_uniq
  - django_content_type_pkey


### Tabela: django_migrations
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             bigint               NO                                       
app                            character varying(255) NO                                       
name                           character varying(255) NO                                       
applied                        timestamp with time zone NO                                       

#### Constraints:
  - PRIMARY KEY: id

#### Índices:
  - django_migrations_pkey


### Tabela: django_session
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
session_key                    character varying(40) NO                                       
session_data                   text                 NO                                       
expire_date                    timestamp with time zone NO                                       

#### Constraints:
  - PRIMARY KEY: session_key

#### Índices:
  - django_session_expire_date_a5c62663
  - django_session_pkey
  - django_session_session_key_c0390e0f_like


### Tabela: exportacoes
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('exportacoes_id_seq'  
cnes                           character varying(7) NO                                       
competencia                    character varying(6) NO                                       
tipo                           character varying(10) NO                                       
arquivo                        character varying(255) YES                                      
total_registros                integer              YES        0                             
status                         character varying(20) YES        'pendente'::character varyin  
erro                           text                 YES                                      
usuario_id                     integer              YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - FOREIGN KEY: usuario_id -> usuarios.id
  - PRIMARY KEY: id

#### Índices:
  - exportacoes_pkey


### Tabela: historico_extracoes
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('historico_extracoes  
cnes                           character varying(7) NO                                       
competencia                    character varying(6) NO                                       
total_bpa_i                    integer              YES        0                             
total_bpa_c                    integer              YES        0                             
total_removido                 integer              YES        0                             
total_geral                    integer              YES        0                             
valor_total_bpa_i              numeric(12,2)        YES        0.00                          
valor_total_bpa_c              numeric(12,2)        YES        0.00                          
valor_total_geral              numeric(12,2)        YES        0.00                          
procedimentos_mais_usados      jsonb                YES                                      
profissionais_mais_ativos      jsonb                YES                                      
distribuicao_por_dia           jsonb                YES                                      
usuario_id                     integer              YES                                      
duracao_segundos               integer              YES                                      
status                         character varying(20) YES        'concluido'::character varyi  
erro                           text                 YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - FOREIGN KEY: usuario_id -> usuarios.id
  - PRIMARY KEY: id

#### Índices:
  - historico_extracoes_pkey
  - idx_historico_cnes
  - idx_historico_competencia
  - idx_historico_created_at


### Tabela: logs
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('logs_id_seq'::regcl  
usuario_id                     integer              YES                                      
acao                           character varying(100) NO                                       
tabela                         character varying(50) YES                                      
registro_id                    integer              YES                                      
dados_anteriores               jsonb                YES                                      
dados_novos                    jsonb                YES                                      
ip                             character varying(45) YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - FOREIGN KEY: usuario_id -> usuarios.id
  - PRIMARY KEY: id

#### Índices:
  - logs_pkey


### Tabela: pacientes
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('pacientes_id_seq'::  
cns                            character varying(15) NO                                       
cpf                            character varying(11) YES                                      
nome                           character varying(255) NO                                       
data_nascimento                character varying(8) YES                                      
sexo                           character varying(1) YES                                      
raca_cor                       character varying(2) YES                                      
nacionalidade                  character varying(3) YES        '010'::character varying      
municipio_ibge                 character varying(6) YES                                      
cep                            character varying(8) YES                                      
logradouro_codigo              character varying(10) YES                                      
endereco                       character varying(255) YES                                      
numero                         character varying(10) YES                                      
complemento                    character varying(100) YES                                      
bairro                         character varying(100) YES                                      
telefone                       character varying(50) YES                                      
email                          character varying(255) YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
updated_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: cns

#### Índices:
  - pacientes_cns_key
  - pacientes_pkey


### Tabela: procedimentos
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('procedimentos_id_se  
codigo                         character varying(10) NO                                       
descricao                      character varying(255) YES                                      
tipo                           character varying(10) YES                                      
valor                          numeric(10,2)        YES                                      
ativo                          boolean              YES        true                          

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: codigo

#### Índices:
  - procedimentos_codigo_key
  - procedimentos_pkey


### Tabela: profissionais
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('profissionais_id_se  
cnes                           character varying(7) NO                                       
cns                            character varying(15) NO                                       
cpf                            character varying(11) YES                                      
nome                           character varying(255) NO                                       
cbo                            character varying(6) NO                                       
ine                            character varying(10) YES                                      
vinculo                        character varying(50) YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
updated_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
conselho                       character varying(20) YES                                      
uf_conselho                    character varying(2) YES                                      

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: cnes
  - UNIQUE: cnes
  - UNIQUE: cns
  - UNIQUE: cns

#### Índices:
  - profissionais_cnes_cns_key
  - profissionais_pkey


### Tabela: sigtap_ocupacao
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
co_ocupacao                    character varying(6) NO                                       
no_ocupacao                    character varying(150) NO                                       
dt_competencia                 character(6)         YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - PRIMARY KEY: co_ocupacao

#### Índices:
  - sigtap_ocupacao_pkey


### Tabela: sigtap_proc_cbo
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
co_procedimento                character varying(10) NO                                       
co_ocupacao                    character varying(6) NO                                       
dt_competencia                 character(6)         YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - FOREIGN KEY: co_ocupacao -> sigtap_ocupacao.co_ocupacao
  - FOREIGN KEY: co_procedimento -> sigtap_procedimento.co_procedimento
  - PRIMARY KEY: co_procedimento
  - PRIMARY KEY: co_ocupacao
  - PRIMARY KEY: co_ocupacao
  - PRIMARY KEY: co_procedimento

#### Índices:
  - idx_proc_cbo_ocupacao
  - sigtap_proc_cbo_pkey


### Tabela: sigtap_proc_registro
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
co_procedimento                character varying(10) NO                                       
co_registro                    character varying(2) NO                                       
dt_competencia                 character(6)         YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - FOREIGN KEY: co_procedimento -> sigtap_procedimento.co_procedimento
  - FOREIGN KEY: co_registro -> sigtap_registro.co_registro
  - PRIMARY KEY: co_registro
  - PRIMARY KEY: co_registro
  - PRIMARY KEY: co_procedimento
  - PRIMARY KEY: co_procedimento

#### Índices:
  - idx_proc_registro_registro
  - sigtap_proc_registro_pkey


### Tabela: sigtap_proc_servico
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
co_procedimento                character varying(10) NO                                       
co_servico                     character varying(3) NO                                       
co_classificacao               character varying(3) NO                                       
dt_competencia                 character(6)         YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - FOREIGN KEY: co_procedimento -> sigtap_procedimento.co_procedimento
  - PRIMARY KEY: co_procedimento
  - PRIMARY KEY: co_procedimento
  - PRIMARY KEY: co_servico
  - PRIMARY KEY: co_servico
  - PRIMARY KEY: co_servico
  - PRIMARY KEY: co_classificacao
  - PRIMARY KEY: co_classificacao
  - PRIMARY KEY: co_classificacao
  - PRIMARY KEY: co_procedimento

#### Índices:
  - idx_proc_servico_servico
  - sigtap_proc_servico_pkey


### Tabela: sigtap_procedimento
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
co_procedimento                character varying(10) NO                                       
no_procedimento                character varying(250) NO                                       
tp_complexidade                character(1)         YES                                      
tp_sexo                        character(1)         YES                                      
qt_maxima_execucao             integer              YES                                      
qt_dias_permanencia            integer              YES                                      
qt_pontos                      integer              YES                                      
vl_idade_minima                integer              YES                                      
vl_idade_maxima                integer              YES                                      
vl_sh                          numeric(10,2)        YES                                      
vl_sa                          numeric(10,2)        YES                                      
vl_sp                          numeric(10,2)        YES                                      
co_financiamento               character varying(2) YES                                      
co_rubrica                     character varying(6) YES                                      
qt_tempo_permanencia           integer              YES                                      
dt_competencia                 character(6)         YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - PRIMARY KEY: co_procedimento

#### Índices:
  - idx_procedimento_nome
  - sigtap_procedimento_pkey


### Tabela: sigtap_registro
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
co_registro                    character varying(2) NO                                       
no_registro                    character varying(50) NO                                       
dt_competencia                 character(6)         YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - PRIMARY KEY: co_registro

#### Índices:
  - sigtap_registro_pkey


### Tabela: sigtap_servico
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
co_servico                     character varying(3) NO                                       
co_classificacao               character varying(3) NO                                       
no_servico_classificacao       character varying(200) NO                                       
dt_competencia                 character(6)         YES                                      
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             

#### Constraints:
  - PRIMARY KEY: co_classificacao
  - PRIMARY KEY: co_servico
  - PRIMARY KEY: co_servico
  - PRIMARY KEY: co_classificacao

#### Índices:
  - sigtap_servico_pkey


### Tabela: usuarios
------------------------------------------------------------

#### Colunas:
Nome                           Tipo                 Nullable   Default                       
------------------------------------------------------------------------------------------
id                             integer              NO         nextval('usuarios_id_seq'::r  
username                       character varying(100) NO                                       
nome                           character varying(255) NO                                       
email                          character varying(255) YES                                      
password_hash                  character varying(255) NO                                       
cnes                           character varying(7) YES                                      
nome_unidade                   character varying(255) YES                                      
perfil                         character varying(50) YES        'digitador'::character varyi  
ativo                          boolean              YES        true                          
created_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
updated_at                     timestamp without time zone YES        CURRENT_TIMESTAMP             
last_login                     timestamp without time zone YES                                      

#### Constraints:
  - PRIMARY KEY: id
  - UNIQUE: username

#### Índices:
  - usuarios_pkey
  - usuarios_username_key


================================================================================
## Sugestões de Models Django
================================================================================

class BpaConsolidado(models.Model):
    """Model para tabela bpa_consolidado."""

    id = models.AutoField(primary_key=True)
    prd_uid = models.CharField(max_length=7)
    prd_cmp = models.CharField(max_length=6)
    prd_flh = models.IntegerField(null=True, blank=True)
    prd_cnsmed = models.CharField(max_length=15)
    prd_cbo = models.CharField(max_length=6)
    prd_pa = models.CharField(max_length=10)
    prd_qt_p = models.IntegerField(null=True, blank=True)
    prd_idade = models.CharField(max_length=3, null=True, blank=True)
    prd_org = models.CharField(max_length=10, null=True, blank=True)
    prd_exportado = models.BooleanField(null=True, blank=True)
    data_exportacao = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bpa_consolidado'
        managed = False


class BpaIndividualizado(models.Model):
    """Model para tabela bpa_individualizado."""

    id = models.AutoField(primary_key=True)
    prd_uid = models.CharField(max_length=7, null=True, blank=True)
    prd_cmp = models.CharField(max_length=6, null=True, blank=True)
    prd_flh = models.IntegerField(null=True, blank=True)
    prd_seq = models.IntegerField(null=True, blank=True)
    prd_cnsmed = models.CharField(max_length=15, null=True, blank=True)
    prd_cbo = models.CharField(max_length=6, null=True, blank=True)
    prd_ine = models.CharField(max_length=10, null=True, blank=True)
    prd_cnspac = models.CharField(max_length=15, null=True, blank=True)
    prd_cpf_pcnte = models.CharField(max_length=11, null=True, blank=True)
    prd_nmpac = models.CharField(max_length=255, null=True, blank=True)
    prd_dtnasc = models.CharField(max_length=8, null=True, blank=True)
    prd_sexo = models.CharField(max_length=1, null=True, blank=True)
    prd_raca = models.CharField(max_length=2, null=True, blank=True)
    prd_nac = models.CharField(max_length=3, null=True, blank=True)
    prd_ibge = models.CharField(max_length=6, null=True, blank=True)
    prd_cep_pcnte = models.CharField(max_length=8, null=True, blank=True)
    prd_lograd_pcnte = models.CharField(max_length=10, null=True, blank=True)
    prd_end_pcnte = models.CharField(max_length=255, null=True, blank=True)
    prd_num_pcnte = models.CharField(max_length=10, null=True, blank=True)
    prd_compl_pcnte = models.CharField(max_length=100, null=True, blank=True)
    prd_bairro_pcnte = models.CharField(max_length=100, null=True, blank=True)
    prd_tel_pcnte = models.CharField(max_length=50, null=True, blank=True)
    prd_email_pcnte = models.CharField(max_length=255, null=True, blank=True)
    prd_dtaten = models.CharField(max_length=8, null=True, blank=True)
    prd_pa = models.CharField(max_length=10, null=True, blank=True)
    prd_qt_p = models.IntegerField(null=True, blank=True)
    prd_cid = models.CharField(max_length=10, null=True, blank=True)
    prd_caten = models.CharField(max_length=2, null=True, blank=True)
    prd_naut = models.CharField(max_length=50, null=True, blank=True)
    prd_cnpj = models.CharField(max_length=14, null=True, blank=True)
    prd_servico = models.CharField(max_length=3, null=True, blank=True)
    prd_classificacao = models.CharField(max_length=3, null=True, blank=True)
    prd_org = models.CharField(max_length=10, null=True, blank=True)
    prd_exportado = models.BooleanField(null=True, blank=True)
    data_exportacao = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    prd_idade = models.CharField(max_length=3, null=True, blank=True)
    prd_ddtel_pcnte = models.CharField(max_length=2, null=True, blank=True)
    movimento = models.CharField(max_length=6, null=True, blank=True)
    prd_etnia = models.CharField(max_length=4, null=True, blank=True)
    prd_eqp_area = models.CharField(max_length=10, null=True, blank=True)
    prd_eqp_seq = models.CharField(max_length=10, null=True, blank=True)
    advqt = models.CharField(max_length=2, null=True, blank=True)
    fl_pa = models.CharField(max_length=1, null=True, blank=True)
    fl_cbo = models.CharField(max_length=1, null=True, blank=True)
    fl_ca = models.CharField(max_length=1, null=True, blank=True)
    fl_ida = models.CharField(max_length=1, null=True, blank=True)
    fl_qt = models.CharField(max_length=1, null=True, blank=True)
    fl_er = models.CharField(max_length=1, null=True, blank=True)
    fl_mun = models.CharField(max_length=1, null=True, blank=True)
    fl_cid = models.CharField(max_length=1, null=True, blank=True)
    prd_mvm = models.CharField(max_length=6, null=True, blank=True)
    prd_advqt = models.CharField(max_length=2, null=True, blank=True)
    prd_flpa = models.CharField(max_length=1, null=True, blank=True)
    prd_flcbo = models.CharField(max_length=1, null=True, blank=True)
    prd_flca = models.CharField(max_length=1, null=True, blank=True)
    prd_flida = models.CharField(max_length=1, null=True, blank=True)
    prd_flqt = models.CharField(max_length=1, null=True, blank=True)
    prd_fler = models.CharField(max_length=1, null=True, blank=True)
    prd_flmun = models.CharField(max_length=1, null=True, blank=True)
    prd_flcid = models.CharField(max_length=1, null=True, blank=True)

    class Meta:
        db_table = 'bpa_individualizado'
        managed = False


class Cbo(models.Model):
    """Model para tabela cbo."""

    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=6)
    descricao = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'cbo'
        managed = False


class Cid(models.Model):
    """Model para tabela cid."""

    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=10)
    descricao = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'cid'
        managed = False


class Exportacoes(models.Model):
    """Model para tabela exportacoes."""

    id = models.AutoField(primary_key=True)
    cnes = models.CharField(max_length=7)
    competencia = models.CharField(max_length=6)
    tipo = models.CharField(max_length=10)
    arquivo = models.CharField(max_length=255, null=True, blank=True)
    total_registros = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    erro = models.TextField(null=True, blank=True)
    usuario_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'exportacoes'
        managed = False


class HistoricoExtracoes(models.Model):
    """Model para tabela historico_extracoes."""

    id = models.AutoField(primary_key=True)
    cnes = models.CharField(max_length=7)
    competencia = models.CharField(max_length=6)
    total_bpa_i = models.IntegerField(null=True, blank=True)
    total_bpa_c = models.IntegerField(null=True, blank=True)
    total_removido = models.IntegerField(null=True, blank=True)
    total_geral = models.IntegerField(null=True, blank=True)
    valor_total_bpa_i = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    valor_total_bpa_c = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    valor_total_geral = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    procedimentos_mais_usados = models.JSONField(null=True, blank=True)
    profissionais_mais_ativos = models.JSONField(null=True, blank=True)
    distribuicao_por_dia = models.JSONField(null=True, blank=True)
    usuario_id = models.IntegerField(null=True, blank=True)
    duracao_segundos = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    erro = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'historico_extracoes'
        managed = False


class Logs(models.Model):
    """Model para tabela logs."""

    id = models.AutoField(primary_key=True)
    usuario_id = models.IntegerField(null=True, blank=True)
    acao = models.CharField(max_length=100)
    tabela = models.CharField(max_length=50, null=True, blank=True)
    registro_id = models.IntegerField(null=True, blank=True)
    dados_anteriores = models.JSONField(null=True, blank=True)
    dados_novos = models.JSONField(null=True, blank=True)
    ip = models.CharField(max_length=45, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'logs'
        managed = False


class Pacientes(models.Model):
    """Model para tabela pacientes."""

    id = models.AutoField(primary_key=True)
    cns = models.CharField(max_length=15)
    cpf = models.CharField(max_length=11, null=True, blank=True)
    nome = models.CharField(max_length=255)
    data_nascimento = models.CharField(max_length=8, null=True, blank=True)
    sexo = models.CharField(max_length=1, null=True, blank=True)
    raca_cor = models.CharField(max_length=2, null=True, blank=True)
    nacionalidade = models.CharField(max_length=3, null=True, blank=True)
    municipio_ibge = models.CharField(max_length=6, null=True, blank=True)
    cep = models.CharField(max_length=8, null=True, blank=True)
    logradouro_codigo = models.CharField(max_length=10, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    telefone = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pacientes'
        managed = False


class Procedimentos(models.Model):
    """Model para tabela procedimentos."""

    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=10)
    descricao = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.CharField(max_length=10, null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ativo = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = 'procedimentos'
        managed = False


class Profissionais(models.Model):
    """Model para tabela profissionais."""

    id = models.AutoField(primary_key=True)
    cnes = models.CharField(max_length=7)
    cns = models.CharField(max_length=15)
    cpf = models.CharField(max_length=11, null=True, blank=True)
    nome = models.CharField(max_length=255)
    cbo = models.CharField(max_length=6)
    ine = models.CharField(max_length=10, null=True, blank=True)
    vinculo = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    conselho = models.CharField(max_length=20, null=True, blank=True)
    uf_conselho = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        db_table = 'profissionais'
        managed = False


class SigtapOcupacao(models.Model):
    """Model para tabela sigtap_ocupacao."""

    co_ocupacao = models.CharField(max_length=6)
    no_ocupacao = models.CharField(max_length=150)
    dt_competencia = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sigtap_ocupacao'
        managed = False


class SigtapProcCbo(models.Model):
    """Model para tabela sigtap_proc_cbo."""

    co_procedimento = models.CharField(max_length=10)
    co_ocupacao = models.CharField(max_length=6)
    dt_competencia = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sigtap_proc_cbo'
        managed = False


class SigtapProcRegistro(models.Model):
    """Model para tabela sigtap_proc_registro."""

    co_procedimento = models.CharField(max_length=10)
    co_registro = models.CharField(max_length=2)
    dt_competencia = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sigtap_proc_registro'
        managed = False


class SigtapProcServico(models.Model):
    """Model para tabela sigtap_proc_servico."""

    co_procedimento = models.CharField(max_length=10)
    co_servico = models.CharField(max_length=3)
    co_classificacao = models.CharField(max_length=3)
    dt_competencia = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sigtap_proc_servico'
        managed = False


class SigtapProcedimento(models.Model):
    """Model para tabela sigtap_procedimento."""

    co_procedimento = models.CharField(max_length=10)
    no_procedimento = models.CharField(max_length=250)
    tp_complexidade = models.CharField(max_length=1, null=True, blank=True)
    tp_sexo = models.CharField(max_length=1, null=True, blank=True)
    qt_maxima_execucao = models.IntegerField(null=True, blank=True)
    qt_dias_permanencia = models.IntegerField(null=True, blank=True)
    qt_pontos = models.IntegerField(null=True, blank=True)
    vl_idade_minima = models.IntegerField(null=True, blank=True)
    vl_idade_maxima = models.IntegerField(null=True, blank=True)
    vl_sh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vl_sa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vl_sp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    co_financiamento = models.CharField(max_length=2, null=True, blank=True)
    co_rubrica = models.CharField(max_length=6, null=True, blank=True)
    qt_tempo_permanencia = models.IntegerField(null=True, blank=True)
    dt_competencia = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sigtap_procedimento'
        managed = False


class SigtapRegistro(models.Model):
    """Model para tabela sigtap_registro."""

    co_registro = models.CharField(max_length=2)
    no_registro = models.CharField(max_length=50)
    dt_competencia = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sigtap_registro'
        managed = False


class SigtapServico(models.Model):
    """Model para tabela sigtap_servico."""

    co_servico = models.CharField(max_length=3)
    co_classificacao = models.CharField(max_length=3)
    no_servico_classificacao = models.CharField(max_length=200)
    dt_competencia = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sigtap_servico'
        managed = False


class Usuarios(models.Model):
    """Model para tabela usuarios."""

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    nome = models.CharField(max_length=255)
    email = models.CharField(max_length=255, null=True, blank=True)
    password_hash = models.CharField(max_length=255)
    cnes = models.CharField(max_length=7, null=True, blank=True)
    nome_unidade = models.CharField(max_length=255, null=True, blank=True)
    perfil = models.CharField(max_length=50, null=True, blank=True)
    ativo = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'usuarios'
        managed = False

