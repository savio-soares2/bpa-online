"""
Lista de estabelecimentos de saúde cadastrados
CNES e nomes das unidades

Mapeamento para SIGTAP:
- Cada tipo de estabelecimento está associado a serviços SIGTAP específicos
- Isso permite filtrar apenas os procedimentos válidos para cada tipo de unidade
- Serviços SIGTAP (tb_servico.txt):
    115 = Atenção Psicossocial (CAPS)
    114 = Saúde Bucal (CEO)
    140 = Urgência e Emergência (UPA)
    126 = Fisioterapia (Centro de Reabilitação)
    145 = Diagnóstico Laboratório (Laboratório)
    E outros conforme classificação CNES
"""

# Mapeamento TIPO_ESTABELECIMENTO -> SERVIÇOS SIGTAP
# Cada tipo pode ter múltiplos serviços associados
TIPO_ESTABELECIMENTO_SERVICOS = {
    "CAPS": {
        "servicos": ["115"],  # 115 = Atenção Psicossocial
        "classificacoes": ["001", "002", "006", "007", "011"],  # CAPS I, II, III, AD, i
        "descricao": "Centro de Atenção Psicossocial"
    },
    "CEO": {
        "servicos": [],  # Alterado para vazio: permite todos procedimentos ambulatoriais (sem filtro de serviço)
        "classificacoes": ["001", "002", "003", "004", "005", "006", "007", "008"],
        "descricao": "Centro de Especialidades Odontológicas"
    },
    "UPA": {
        "servicos": ["140"],  # 140 = Urgência e Emergência
        "classificacoes": ["004", "005", "006", "007", "008", "009"],
        "descricao": "Unidade de Pronto Atendimento"
    },
    "AMBULATORIO": {
        "servicos": [],  # Aceita todos os procedimentos ambulatoriais (VL_SA > 0)
        "classificacoes": [],
        "descricao": "Ambulatório Geral - aceita todos procedimentos ambulatoriais"
    },
    "POLICLINICA": {
        "servicos": [],  # Aceita todos os procedimentos ambulatoriais (VL_SA > 0)
        "classificacoes": [],
        "descricao": "Policlínica - aceita todos procedimentos ambulatoriais"
    },
    "CENTRO_REF": {
        "servicos": ["126", "135"],  # 126 = Fisioterapia, 135 = Reabilitação
        "classificacoes": [],
        "descricao": "Centro de Referência em Reabilitação/Fisioterapia"
    },
    "LABORATORIO": {
        "servicos": ["145", "120"],  # 145 = Lab Clínico, 120 = Anatomia Patológica
        "classificacoes": [],
        "descricao": "Laboratório de Análises/Prótese"
    }
}

# Código IBGE do município padrão (Palmas-TO)
IBGE_MUNICIPIO_PADRAO = "172100"

ESTABELECIMENTOS = [
    {
        "cnes": "6061478",
        "nome": "CAPS AD - Centro de Atenção Psicossocial Álcool e Outras Drogas",
        "sigla": "CAPS AD",
        "tipo": "CAPS",
        "servico_sigtap": "115",
        "classificacao_sigtap": "002",  # Atendimento psicossocial
        "ibge_municipio": "172100"  # Palmas-TO
    },
    {
        "cnes": "2467968",
        "nome": "CAPS II - Centro de Atenção Psicossocial",
        "sigla": "CAPS II",
        "tipo": "CAPS",
        "servico_sigtap": "115",
        "classificacao_sigtap": "002",
        "ibge_municipio": "172100"
    },
    {
        "cnes": "4392388",
        "nome": "CAPSi - Centro de Atenção Psicossocial Inf. Juven. Dr. Emílio Fernandes",
        "sigla": "CAPSi",
        "tipo": "CAPS",
        "servico_sigtap": "115",
        "classificacao_sigtap": "007",  # Infantojuvenil
        "ibge_municipio": "172100"
    },
    {
        "cnes": "5504694",
        "nome": "Ambulatório Municipal de Atenção à Saúde Dr. Eduardo Medrado",
        "sigla": "Amb. Eduardo Medrado",
        "tipo": "AMBULATORIO",
        "servico_sigtap": None,  # Aceita todos ambulatoriais
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    },
    {
        "cnes": "2467925",
        "nome": "Núcleo de Assistência Henfil",
        "sigla": "Henfil",
        "tipo": "AMBULATORIO",
        "servico_sigtap": None,
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    },
    {
        "cnes": "2492482",
        "nome": "Centro de Atenção Esp. à Saúde Francisca Romana Chaves",
        "sigla": "CAES Francisca Romana",
        "tipo": "AMBULATORIO",
        "servico_sigtap": None,
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    },
    {
        "cnes": "2492563",
        "nome": "Policlínica de Taquaralto",
        "sigla": "Polic. Taquaralto",
        "tipo": "POLICLINICA",
        "servico_sigtap": None,
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    },
    {
        "cnes": "2492547",
        "nome": "Centro de Especialidades Odontológicas",
        "sigla": "CEO",
        "tipo": "CEO",
        "servico_sigtap": None, # Alterado para None: permite todos procedimentos ambulatoriais
        "classificacao_sigtap": None,  # Todas as classificações de saúde bucal
        "ibge_municipio": "172100"
    },
    {
        "cnes": "6425348",
        "nome": "Laboratório Regional de Prótese Dentária de Palmas",
        "sigla": "Lab. Prótese",
        "tipo": "LABORATORIO",
        "servico_sigtap": "145",
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    },
    {
        "cnes": "7759290",
        "nome": "CREFISUL - Centro de Referência em Fisioterapia da Região Sul",
        "sigla": "CREFISUL",
        "tipo": "CENTRO_REF",
        "servico_sigtap": "126",  # Fisioterapia
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    },
    {
        "cnes": "2755289",
        "nome": "Unidade de Pronto Atendimento Norte",
        "sigla": "UPA Norte",
        "tipo": "UPA",
        "servico_sigtap": "140",
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    },
    {
        "cnes": "2492555",
        "nome": "Unidade de Pronto Atendimento Sul",
        "sigla": "UPA Sul",
        "tipo": "UPA",
        "servico_sigtap": "140",
        "classificacao_sigtap": None,
        "ibge_municipio": "172100"
    }
]

# Lista de CNES válidos
CNES_VALIDOS = [e["cnes"] for e in ESTABELECIMENTOS]

def get_estabelecimento(cnes: str) -> dict | None:
    """Retorna estabelecimento pelo CNES"""
    for e in ESTABELECIMENTOS:
        if e["cnes"] == cnes:
            return e
    return None

def get_nome_estabelecimento(cnes: str) -> str:
    """Retorna nome do estabelecimento pelo CNES"""
    e = get_estabelecimento(cnes)
    return e["sigla"] if e else cnes

def get_tipo_estabelecimento(cnes: str) -> str | None:
    """Retorna o tipo de estabelecimento pelo CNES"""
    e = get_estabelecimento(cnes)
    return e["tipo"] if e else None

def get_servico_sigtap(cnes: str) -> str | None:
    """Retorna o código de serviço SIGTAP do estabelecimento"""
    e = get_estabelecimento(cnes)
    return e.get("servico_sigtap") if e else None

def get_classificacao_sigtap(cnes: str) -> str | None:
    """Retorna a classificação SIGTAP do estabelecimento"""
    e = get_estabelecimento(cnes)
    return e.get("classificacao_sigtap") if e else None

def get_ibge_municipio(cnes: str) -> str:
    """Retorna o código IBGE do município do estabelecimento"""
    e = get_estabelecimento(cnes)
    if e and e.get("ibge_municipio"):
        return e["ibge_municipio"]
    return IBGE_MUNICIPIO_PADRAO

def get_servicos_por_tipo(tipo: str) -> list:
    """Retorna lista de serviços SIGTAP para um tipo de estabelecimento"""
    config = TIPO_ESTABELECIMENTO_SERVICOS.get(tipo, {})
    return config.get("servicos", [])

def get_classificacoes_por_tipo(tipo: str) -> list:
    """Retorna lista de classificações SIGTAP para um tipo de estabelecimento"""
    config = TIPO_ESTABELECIMENTO_SERVICOS.get(tipo, {})
    return config.get("classificacoes", [])

def is_cnes_valido(cnes: str) -> bool:
    """Verifica se CNES é válido"""
    return cnes in CNES_VALIDOS

def is_ambulatorio_geral(cnes: str) -> bool:
    """
    Verifica se o estabelecimento aceita todos os procedimentos ambulatoriais.
    Estabelecimentos como Ambulatório e Policlínica não têm serviço específico,
    aceitam qualquer procedimento com VL_SA > 0.
    """
    tipo = get_tipo_estabelecimento(cnes)
    return tipo in ("AMBULATORIO", "POLICLINICA")
