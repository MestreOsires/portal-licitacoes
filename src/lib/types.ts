export interface Licitacao {
  id: string;
  orgao: string;
  objeto: string;
  valor_estimado: number | null;
  data_disputa: string | null;
  link_edital: string | null;
  municipio: string;
  estado: string;
  coordenadas?: string | null;
  fonte: string;
  id_externo?: string;
  created_at?: string;
  // Campos derivados do padrão Universo Licitações
  modalidade?: string;
  regiao?: "Norte" | "Nordeste" | "Centro-Oeste" | "Sudeste" | "Sul" | string;
  esfera?: "Federal" | "Estadual" | "Municipal" | string;
  tipo_publicacao?: "AVISO" | "RESULTADO" | "AGENDA" | "COTACAO" | string;
  numero_processo?: string;
}

export interface FiltrosLicitacao {
  busca?: string;
  estado?: string;
  municipio?: string;
  regiao?: string;
  modalidade?: string;
  esfera?: string;
  tipoPublicacao?: string; // "TODOS" | "AVISO" | "RESULTADO" | "AGENDA" | "COTACAO"
  periodoAgenda?: string; // "todos" | "hoje" | "amanha" | "7dias" | "30dias"
  valorMin?: number;
  valorMax?: number;
  fonte?: string;
  ordenacao?: "disputa_asc" | "disputa_desc" | "valor_asc" | "valor_desc" | "recentes";
  pagina?: number;
  limite?: number;
}

export interface PlacarDoDia {
  totalLicitacoes: number;
  totalResultados: number;
  totalValor: number;
  totalCotacoes: number;
}

export interface AlertaCadastro {
  nome: string;
  telefone_whatsapp: string;
  palavras_chave: string[];
  municipio_base: string;
  estado_base?: string;
  raio_km: number;
}
