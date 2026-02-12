/**
 * Lista de estabelecimentos de saúde cadastrados
 * CNES e nomes das unidades para seleção nas telas
 */

export interface Estabelecimento {
  cnes: string;
  nome: string;
  sigla: string;
  tipo: 'CAPS' | 'AMBULATORIO' | 'POLICLINICA' | 'UPA' | 'CEO' | 'LABORATORIO' | 'CENTRO_REF';
}

export const ESTABELECIMENTOS: Estabelecimento[] = [
  {
    cnes: '6061478',
    nome: 'CAPS AD - Centro de Atenção Psicossocial Álcool e Outras Drogas',
    sigla: 'CAPS AD',
    tipo: 'CAPS'
  },
  {
    cnes: '2467968',
    nome: 'CAPS II - Centro de Atenção Psicossocial',
    sigla: 'CAPS II',
    tipo: 'CAPS'
  },
  {
    cnes: '4392388',
    nome: 'CAPSi - Centro de Atenção Psicossocial Inf. Juven. Dr. Emílio Fernandes',
    sigla: 'CAPSi',
    tipo: 'CAPS'
  },
  {
    cnes: '5504694',
    nome: 'Ambulatório Municipal de Atenção à Saúde Dr. Eduardo Medrado',
    sigla: 'Amb. Eduardo Medrado',
    tipo: 'AMBULATORIO'
  },
  {
    cnes: '2467925',
    nome: 'CENTRO DE ATENCAO ESPECIALIZADA A SAUDE DR EWALDO BORGES RES',
    sigla: 'CAES Ewaldo Borges',
    tipo: 'AMBULATORIO'
  },
  {
    cnes: '2492482',
    nome: 'Centro de Atenção Esp. à Saúde Francisca Romana Chaves',
    sigla: 'CAES Francisca Romana',
    tipo: 'AMBULATORIO'
  },
  {
    cnes: '2492563',
    nome: 'Policlínica de Taquaralto',
    sigla: 'Polic. Taquaralto',
    tipo: 'POLICLINICA'
  },
  {
    cnes: '2492547',
    nome: 'Centro de Especialidades Odontológicas',
    sigla: 'CEO',
    tipo: 'CEO'
  },
  {
    cnes: '6425348',
    nome: 'Laboratório Regional de Prótese Dentária de Palmas',
    sigla: 'Lab. Prótese',
    tipo: 'LABORATORIO'
  },
  {
    cnes: '7759290',
    nome: 'CREFISUL - Centro de Referência em Fisioterapia da Região Sul',
    sigla: 'CREFISUL',
    tipo: 'CENTRO_REF'
  },
  {
    cnes: '2755289',
    nome: 'Unidade de Pronto Atendimento Norte',
    sigla: 'UPA Norte',
    tipo: 'UPA'
  },
  {
    cnes: '2492555',
    nome: 'Unidade de Pronto Atendimento Sul',
    sigla: 'UPA Sul',
    tipo: 'UPA'
  }
];

// Função helper para buscar estabelecimento por CNES
export const getEstabelecimentoByCnes = (cnes: string): Estabelecimento | undefined => {
  return ESTABELECIMENTOS.find(e => e.cnes === cnes);
};

// Função helper para obter nome curto
export const getNomeEstabelecimento = (cnes: string): string => {
  const estab = getEstabelecimentoByCnes(cnes);
  return estab?.sigla || estab?.nome || cnes;
};
