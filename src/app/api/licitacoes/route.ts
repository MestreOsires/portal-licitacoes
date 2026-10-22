import { NextResponse } from "next/server";
import { supabase, isSupabaseConfigured } from "@/lib/supabaseClient";
import { Licitacao, PlacarDoDia } from "@/lib/types";
import { extrairListaRadicais, correspondeRadicais, UF_REGIAO_MAP, removerAcentos } from "@/lib/searchUtils";

// Base de dados expandida com padrão do Universo Licitações
const DADOS_EXEMPLO: Licitacao[] = [
  // --- MARANHÃO (MA - NORTE/NORDESTE) ---
  {
    id: "ma-1",
    orgao: "Prefeitura Municipal de São Luís",
    objeto: "Registro de preços para aquisição de kits pedagógicos e mobiliário escolar para a rede de ensino fundamental de São Luís.",
    valor_estimado: 3250000.0,
    data_disputa: new Date(Date.now() + 86400000 * 3).toISOString(),
    link_edital: "https://saoluis.ma.gov.br/editais",
    municipio: "São Luís",
    estado: "MA",
    modalidade: "Pregão Eletrônico",
    regiao: "Nordeste",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 042/2026-PMSL",
    fonte: "DIARIO_OFICIAL",
    id_externo: "DO_MA_042"
  },
  {
    id: "ma-2",
    orgao: "Secretaria de Estado da Saúde do Maranhão (SES-MA)",
    objeto: "Contratação de empresa especializada em manutenção preventiva e corretiva de equipamentos de hemodiálise e UTI.",
    valor_estimado: 5120000.0,
    data_disputa: new Date(Date.now() + 86400000 * 12).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Imperatriz",
    estado: "MA",
    modalidade: "Concorrência Eletrônica",
    regiao: "Nordeste",
    esfera: "Estadual",
    tipo_publicacao: "AVISO",
    numero_processo: "CC Nº 105/2026",
    fonte: "PNCP",
    id_externo: "PNCP_MA_2026_01"
  },

  // --- PARÁ (PA - NORTE) ---
  {
    id: "pa-1",
    orgao: "Prefeitura Municipal de Santarém",
    objeto: "Contratação de serviços de transporte escolar fluvial e terrestre para atender alunos da zona ribeirinha.",
    valor_estimado: 4780000.0,
    data_disputa: new Date(Date.now() + 86400000 * 7).toISOString(),
    link_edital: "https://santarem.pa.gov.br",
    municipio: "Santarém",
    estado: "PA",
    modalidade: "Pregão Eletrônico",
    regiao: "Norte",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 088/2026-SEMED",
    fonte: "DIARIO_OFICIAL",
    id_externo: "DO_PA_088"
  },
  {
    id: "pa-2",
    orgao: "Secretaria de Estado de Transportes do Pará (SETRAN-PA)",
    objeto: "Obras de pavimentação asfáltica, terraplenagem e construção de pontes de concreto na rodovia PA-150.",
    valor_estimado: 12450000.0,
    data_disputa: new Date(Date.now() + 86400000 * 18).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Belém",
    estado: "PA",
    modalidade: "Concorrência Eletrônica",
    regiao: "Norte",
    esfera: "Estadual",
    tipo_publicacao: "AVISO",
    numero_processo: "CO Nº 012/2026",
    fonte: "PNCP",
    id_externo: "PNCP_PA_2026_02"
  },

  // --- TOCANTINS (TO - NORTE) ---
  {
    id: "to-1",
    orgao: "Prefeitura Municipal de Palmas",
    objeto: "Obras de drenagem pluvial, pavimentação em CBUQ e sinalização viária nas quadras industriais de Palmas.",
    valor_estimado: 7920000.0,
    data_disputa: new Date(Date.now() + 86400000 * 5).toISOString(),
    link_edital: "https://palmas.to.gov.br",
    municipio: "Palmas",
    estado: "TO",
    modalidade: "Concorrência Eletrônica",
    regiao: "Norte",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "CE Nº 015/2026",
    fonte: "DIARIO_OFICIAL",
    id_externo: "DO_TO_015"
  },
  {
    id: "to-2",
    orgao: "Hospital Regional de Araguaína (SESAU-TO)",
    objeto: "Aquisição de medicamentos oncológicos e insumos de nutrição enteral para o Hospital de Doenças Tropicais.",
    valor_estimado: 2180000.0,
    data_disputa: new Date(Date.now() + 86400000 * 1).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Araguaína",
    estado: "TO",
    modalidade: "Pregão Eletrônico",
    regiao: "Norte",
    esfera: "Estadual",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 033/2026",
    fonte: "PNCP",
    id_externo: "PNCP_TO_2026_01"
  },

  // --- DEMAIS ESTADOS E RESULTADOS/COTAÇÕES (ESTILO UNIVERSO) ---
  {
    id: "sp-1",
    orgao: "Prefeitura Municipal de Campinas",
    objeto: "Aquisição de equipamentos hospitalares, monitores multiparamétricos e respiradores para as UPAs municipais.",
    valor_estimado: 1850000.0,
    data_disputa: new Date(Date.now() + 86400000 * 2).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Campinas",
    estado: "SP",
    modalidade: "Pregão Eletrônico",
    regiao: "Sudeste",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 102/2026",
    fonte: "PNCP",
    id_externo: "PNCP_2026_01"
  },
  {
    id: "sp-res-1",
    orgao: "Tribunal de Justiça do Estado de São Paulo",
    objeto: "Resultado de Homologação: Contratação de licenças de software de cibersegurança e suporte técnico especializado.",
    valor_estimado: 3890000.0,
    data_disputa: new Date(Date.now() - 86400000 * 2).toISOString(),
    link_edital: "https://tjsp.jus.br",
    municipio: "São Paulo",
    estado: "SP",
    modalidade: "Pregão Eletrônico",
    regiao: "Sudeste",
    esfera: "Estadual",
    tipo_publicacao: "RESULTADO",
    numero_processo: "HOMOLOGAÇÃO PE 55/2026",
    fonte: "DIARIO_OFICIAL",
    id_externo: "DO_SP_HOMOLOG_55"
  },
  {
    id: "df-1",
    orgao: "Tribunal Regional Federal da 1ª Região",
    objeto: "Contratação de serviços continuados de suporte técnico em nuvem e segurança da informação.",
    valor_estimado: 4320000.0,
    data_disputa: new Date(Date.now() + 86400000 * 14).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Brasília",
    estado: "DF",
    modalidade: "Pregão Eletrônico",
    regiao: "Centro-Oeste",
    esfera: "Federal",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 019/2026",
    fonte: "PNCP",
    id_externo: "PNCP_2026_02"
  },
  {
    id: "mg-cot-1",
    orgao: "Instituto de Previdência dos Servidores de Minas Gerais (IPSEMG)",
    objeto: "Dispensa de Licitação / Cotação Eletrônica: Fornecimento emergencial de insumos para diagnóstico laboratorial.",
    valor_estimado: 89000.0,
    data_disputa: new Date(Date.now() + 86400000 * 1).toISOString(),
    link_edital: "https://compras.mg.gov.br",
    municipio: "Belo Horizonte",
    estado: "MG",
    modalidade: "Dispensa Eletrônica",
    regiao: "Sudeste",
    esfera: "Estadual",
    tipo_publicacao: "COTACAO",
    numero_processo: "DISPENSA Nº 008/2026",
    fonte: "PNCP",
    id_externo: "PNCP_MG_DISP_008"
  },
  {
    id: "pr-1",
    orgao: "Prefeitura Municipal de Curitiba",
    objeto: "Contratação de empresa de engenharia para pavimentação e microdrenagem de vias urbanas com asfalto ecológico.",
    valor_estimado: 6450000.0,
    data_disputa: new Date(Date.now() + 86400000 * 8).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Curitiba",
    estado: "PR",
    modalidade: "Concorrência Eletrônica",
    regiao: "Sul",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "CO Nº 077/2026",
    fonte: "PNCP",
    id_externo: "PNCP_2026_04"
  }
];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const busca = (searchParams.get("busca") || "").trim();
  const estadoParam = (searchParams.get("estado") || "").toUpperCase().trim();
  const regiaoParam = (searchParams.get("regiao") || "").trim();
  const modalidadeParam = (searchParams.get("modalidade") || "").trim();
  const esferaParam = (searchParams.get("esfera") || "").trim();
  const tipoPublicacao = (searchParams.get("tipoPublicacao") || "").toUpperCase().trim();
  const periodoAgenda = (searchParams.get("periodoAgenda") || "todos").toLowerCase().trim();
  const municipio = (searchParams.get("municipio") || "").toLowerCase().trim();
  const valorMin = searchParams.get("valorMin") ? parseFloat(searchParams.get("valorMin")!) : null;
  const valorMax = searchParams.get("valorMax") ? parseFloat(searchParams.get("valorMax")!) : null;
  const fonte = (searchParams.get("fonte") || "").trim();
  const ordenacao = searchParams.get("ordenacao") || "disputa_asc";

  // Radicais extraídos com o mesmo algoritmo reverso do Universo Licitações
  const listaRadicais = extrairListaRadicais(busca);

  // 1. Consulta ao Supabase Live
  if (isSupabaseConfigured && supabase) {
    try {
      let query = supabase.from("licitacoes").select("*");

      if (listaRadicais.length > 0) {
        // Gera filtro com os radicais normalizados
        const orConditions = listaRadicais
          .map((rad) => `objeto.ilike.%${rad}%,orgao.ilike.%${rad}%`)
          .join(",");
        query = query.or(orConditions);
      }

      if (estadoParam && estadoParam !== "TODOS") {
        query = query.eq("estado", estadoParam);
      }
      if (regiaoParam && regiaoParam !== "TODAS") {
        query = query.eq("regiao", regiaoParam);
      }
      if (modalidadeParam && modalidadeParam !== "TODAS") {
        query = query.eq("modalidade", modalidadeParam);
      }
      if (esferaParam && esferaParam !== "TODAS") {
        query = query.eq("esfera", esferaParam);
      }
      if (tipoPublicacao && tipoPublicacao !== "TODOS") {
        query = query.eq("tipo_publicacao", tipoPublicacao);
      }
      if (municipio) {
        query = query.ilike("municipio", `%${municipio}%`);
      }
      if (valorMin !== null) {
        query = query.gte("valor_estimado", valorMin);
      }
      if (valorMax !== null) {
        query = query.lte("valor_estimado", valorMax);
      }
      if (fonte && fonte !== "TODOS") {
        query = query.eq("fonte", fonte);
      }

      // Ordenação
      if (ordenacao === "valor_desc") {
        query = query.order("valor_estimado", { ascending: false });
      } else if (ordenacao === "valor_asc") {
        query = query.order("valor_estimado", { ascending: true });
      } else if (ordenacao === "disputa_desc") {
        query = query.order("data_disputa", { ascending: false });
      } else {
        query = query.order("data_disputa", { ascending: true });
      }

      const { data, error } = await query.limit(100);

      if (!error && data && data.length > 0) {
        const placar: PlacarDoDia = {
          totalLicitacoes: data.filter((d) => d.tipo_publicacao === "AVISO").length,
          totalResultados: data.filter((d) => d.tipo_publicacao === "RESULTADO").length,
          totalCotacoes: data.filter((d) => d.tipo_publicacao === "COTACAO").length,
          totalValor: data.reduce((acc, curr) => acc + (curr.valor_estimado || 0), 0)
        };

        return NextResponse.json({
          licitacoes: data,
          total: data.length,
          placar,
          origem: "supabase"
        });
      }
    } catch (err) {
      console.warn("Aviso ao consultar Supabase, usando dados locais de demonstração:", err);
    }
  }

  // 2. Filtro local no conjunto de dados completo
  let filtrados = [...DADOS_EXEMPLO];

  // Filtro por radicais (Stemming reverso do Universo Licitações)
  if (listaRadicais.length > 0) {
    filtrados = filtrados.filter((item) =>
      correspondeRadicais(`${item.objeto} ${item.orgao} ${item.numero_processo || ""}`, listaRadicais)
    );
  }

  // Filtro de Estado (UF)
  if (estadoParam && estadoParam !== "TODOS") {
    filtrados = filtrados.filter((item) => item.estado.toUpperCase() === estadoParam);
  }

  // Filtro por Macro-Região
  if (regiaoParam && regiaoParam !== "TODAS") {
    filtrados = filtrados.filter((item) => {
      const regItem = item.regiao || UF_REGIAO_MAP[item.estado] || "Outros";
      return regItem === regiaoParam;
    });
  }

  // Filtro por Modalidade
  if (modalidadeParam && modalidadeParam !== "TODAS") {
    filtrados = filtrados.filter((item) => item.modalidade === modalidadeParam);
  }

  // Filtro por Esfera
  if (esferaParam && esferaParam !== "TODAS") {
    filtrados = filtrados.filter((item) => item.esfera === esferaParam);
  }

  // Filtro por Tipo de Publicação (Avisos, Resultados, Cotações, Agenda)
  if (tipoPublicacao && tipoPublicacao !== "TODOS") {
    filtrados = filtrados.filter((item) => item.tipo_publicacao === tipoPublicacao);
  }

  // Filtro por Município
  if (municipio) {
    filtrados = filtrados.filter((item) =>
      removerAcentos(item.municipio).includes(removerAcentos(municipio))
    );
  }

  // Filtro por Faixa de Valor
  if (valorMin !== null) {
    filtrados = filtrados.filter((item) => (item.valor_estimado || 0) >= valorMin);
  }
  if (valorMax !== null) {
    filtrados = filtrados.filter((item) => (item.valor_estimado || 0) <= valorMax);
  }

  // Filtro por Fonte
  if (fonte && fonte !== "TODOS") {
    filtrados = filtrados.filter((item) => item.fonte === fonte);
  }

  // Filtro de Agenda Cronológica
  if (periodoAgenda && periodoAgenda !== "todos") {
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);

    filtrados = filtrados.filter((item) => {
      if (!item.data_disputa) return false;
      const dtDisputa = new Date(item.data_disputa);
      const diffDias = Math.ceil((dtDisputa.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));

      if (periodoAgenda === "hoje") return diffDias === 0;
      if (periodoAgenda === "amanha") return diffDias === 1;
      if (periodoAgenda === "7dias") return diffDias >= 0 && diffDias <= 7;
      if (periodoAgenda === "30dias") return diffDias >= 0 && diffDias <= 30;
      return true;
    });
  }

  // Ordenação
  filtrados.sort((a, b) => {
    if (ordenacao === "valor_desc") {
      return (b.valor_estimado || 0) - (a.valor_estimado || 0);
    }
    if (ordenacao === "valor_asc") {
      return (a.valor_estimado || 0) - (b.valor_estimado || 0);
    }
    if (ordenacao === "disputa_desc") {
      return new Date(b.data_disputa || 0).getTime() - new Date(a.data_disputa || 0).getTime();
    }
    // disputa_asc padrão
    return new Date(a.data_disputa || 0).getTime() - new Date(b.data_disputa || 0).getTime();
  });

  // Cálculo do Placar do Dia (Métricas Universais)
  const placar: PlacarDoDia = {
    totalLicitacoes: filtrados.filter((d) => d.tipo_publicacao === "AVISO").length,
    totalResultados: filtrados.filter((d) => d.tipo_publicacao === "RESULTADO").length,
    totalCotacoes: filtrados.filter((d) => d.tipo_publicacao === "COTACAO").length,
    totalValor: filtrados.reduce((acc, curr) => acc + (curr.valor_estimado || 0), 0)
  };

  return NextResponse.json({
    licitacoes: filtrados,
    total: filtrados.length,
    placar,
    origem: "demonstracao"
  });
}
