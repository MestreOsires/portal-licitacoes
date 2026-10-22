import { NextResponse } from "next/server";
import { supabase, isSupabaseConfigured } from "@/lib/supabaseClient";
import { Licitacao, PlacarDoDia } from "@/lib/types";
import { extrairListaRadicais, correspondeRadicais, UF_REGIAO_MAP, removerAcentos } from "@/lib/searchUtils";

// Base de dados de demonstração (usada apenas como fallback quando o Supabase estiver desconectado)
const DADOS_EXEMPLO: Licitacao[] = [
  // --- MARANHÃO (MA) ---
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
    fonte: "PNCP",
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
  {
    id: "ma-3",
    orgao: "Prefeitura Municipal de São João dos Patos",
    objeto: "Aquisição de medicamentos básicos, correlatos e material penso para a Secretaria Municipal de Saúde de São João dos Patos.",
    valor_estimado: 890000.0,
    data_disputa: new Date(Date.now() + 86400000 * 4).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "São João dos Patos",
    estado: "MA",
    modalidade: "Pregão Eletrônico",
    regiao: "Nordeste",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 014/2026-PMSJP",
    fonte: "PNCP",
    id_externo: "PNCP_MA_2026_03"
  },

  // --- PARÁ (PA) ---
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
    fonte: "PNCP",
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
  {
    id: "pa-3",
    orgao: "Prefeitura Municipal de Marabá",
    objeto: "Contratação de empresa para reforma e ampliação de unidades básicas de saúde no núcleo Cidade Nova.",
    valor_estimado: 2150000.0,
    data_disputa: new Date(Date.now() + 86400000 * 6).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Marabá",
    estado: "PA",
    modalidade: "Pregão Eletrônico",
    regiao: "Norte",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 031/2026-PMM",
    fonte: "PNCP",
    id_externo: "PNCP_PA_2026_03"
  },

  // --- TOCANTINS (TO) ---
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
    fonte: "PNCP",
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
  {
    id: "to-3",
    orgao: "Município de Riachinho",
    objeto: "Registro de preço para futura e eventual aquisição de gêneros alimentícios, material de limpeza e higienização para a Prefeitura de Riachinho.",
    valor_estimado: 450000.0,
    data_disputa: new Date(Date.now() + 86400000 * 8).toISOString(),
    link_edital: "https://pncp.gov.br",
    municipio: "Riachinho",
    estado: "TO",
    modalidade: "Pregão Eletrônico",
    regiao: "Norte",
    esfera: "Municipal",
    tipo_publicacao: "AVISO",
    numero_processo: "PE Nº 01/2026",
    fonte: "PNCP",
    id_externo: "PNCP_TO_2026_03"
  },

  // --- DEMAIS ESTADOS ---
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
  const municipioParam = (searchParams.get("municipio") || "").trim();
  const valorMin = searchParams.get("valorMin") ? parseFloat(searchParams.get("valorMin")!) : null;
  const valorMax = searchParams.get("valorMax") ? parseFloat(searchParams.get("valorMax")!) : null;
  const fonte = (searchParams.get("fonte") || "").trim();
  const ordenacao = searchParams.get("ordenacao") || "disputa_asc";
  const pagina = Math.max(1, parseInt(searchParams.get("pagina") || "1"));
  const limite = Math.min(200, Math.max(10, parseInt(searchParams.get("limite") || "60")));

  // 1. CONSULTA AO SUPABASE COM SERVER-SIDE FILTERING (Direto no banco de dados)
  if (isSupabaseConfigured && supabase) {
    try {
      // Inicia a query com contagem exata sem limite de 1.000 linhas
      let query = supabase.from("licitacoes").select("*", { count: "exact" });

      // Filtro obrigatório de Oportunidades Futuras: oculta automaticamente licitações expiradas
      const dataDeHoje = new Date().toISOString();
      query = query.gte("data_disputa", dataDeHoje);

      // Filtro Server-Side de UF / Estado
      if (estadoParam && estadoParam !== "TODOS") {
        query = query.eq("estado", estadoParam);
      }

      // Filtro Server-Side de Município com ilike
      if (municipioParam) {
        query = query.ilike("municipio", `%${municipioParam}%`);
      }

      // Filtro Server-Side de Palavra-chave / Objeto com ilike
      if (busca) {
        // Suporte a múltiplos termos separados por vírgula ou termo único
        const termos = busca.split(/[,;]+/).map((t) => t.trim()).filter(Boolean);
        if (termos.length === 1) {
          query = query.ilike("objeto", `%${termos[0]}%`);
        } else if (termos.length > 1) {
          const orConditions = termos
            .map((termo) => `objeto.ilike.%${termo}%,orgao.ilike.%${termo}%`)
            .join(",");
          query = query.or(orConditions);
        }
      }

      // Filtros adicionais Server-Side
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
      if (valorMin !== null && !isNaN(valorMin)) {
        query = query.gte("valor_estimado", valorMin);
      }
      if (valorMax !== null && !isNaN(valorMax)) {
        query = query.lte("valor_estimado", valorMax);
      }
      if (fonte && fonte !== "TODOS") {
        query = query.eq("fonte", fonte);
      }

      // Filtro cronológico Server-Side para Agenda de Disputa
      if (periodoAgenda && periodoAgenda !== "todos") {
        const agora = new Date();
        const inicioHoje = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate()).toISOString();
        const fimHoje = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate(), 23, 59, 59).toISOString();
        const inicioAmanha = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate() + 1).toISOString();
        const fimAmanha = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate() + 1, 23, 59, 59).toISOString();
        const em7Dias = new Date(agora.getTime() + 7 * 86400000).toISOString();
        const em30Dias = new Date(agora.getTime() + 30 * 86400000).toISOString();

        if (periodoAgenda === "hoje") {
          query = query.gte("data_disputa", inicioHoje).lte("data_disputa", fimHoje);
        } else if (periodoAgenda === "amanha") {
          query = query.gte("data_disputa", inicioAmanha).lte("data_disputa", fimAmanha);
        } else if (periodoAgenda === "7dias") {
          query = query.gte("data_disputa", inicioHoje).lte("data_disputa", em7Dias);
        } else if (periodoAgenda === "30dias") {
          query = query.gte("data_disputa", inicioHoje).lte("data_disputa", em30Dias);
        }
      }

      // Ordenação Server-Side
      if (ordenacao === "valor_desc") {
        query = query.order("valor_estimado", { ascending: false });
      } else if (ordenacao === "valor_asc") {
        query = query.order("valor_estimado", { ascending: true });
      } else if (ordenacao === "disputa_desc") {
        query = query.order("data_disputa", { ascending: false });
      } else if (ordenacao === "recentes") {
        query = query.order("created_at", { ascending: false });
      } else {
        query = query.order("data_disputa", { ascending: true });
      }

      // Paginação Server-Side com range para evitar corte de 1.000 linhas
      const offset = (pagina - 1) * limite;
      query = query.range(offset, offset + limite - 1);

      let { data, count, error } = await query;

      // Resiliência caso o banco esteja com nome de coluna alternativo ('uf' em vez de 'estado')
      if (error && (error.message?.includes("estado") || error.code === "PGRST204")) {
        console.warn("Tentando query de contingência com coluna 'uf'...");
        let fallbackQuery = supabase.from("licitacoes").select("*", { count: "exact" });
        fallbackQuery = fallbackQuery.gte("data_disputa", dataDeHoje);
        if (estadoParam && estadoParam !== "TODOS") {
          fallbackQuery = fallbackQuery.eq("uf", estadoParam);
        }
        if (busca) {
          fallbackQuery = fallbackQuery.ilike("objeto", `%${busca}%`);
        }
        fallbackQuery = fallbackQuery.range(offset, offset + limite - 1);
        const retryResult = await fallbackQuery;
        if (!retryResult.error) {
          data = retryResult.data;
          count = retryResult.count;
          error = null;
        }
      }

      // Se o Supabase retornou dados, usa o resultado legítimo do banco
      if (!error && data !== null && (count ?? data.length) > 0) {
        const totalRegistros = count ?? data.length;
        const licitacoesFormatadas = (data as Licitacao[]).map((item) => ({
          ...item,
          estado: item.estado || (item as unknown as { uf?: string }).uf || "",
          municipio: item.municipio || (item as unknown as { cidade?: string }).cidade || ""
        }));

        const placar: PlacarDoDia = {
          totalLicitacoes: licitacoesFormatadas.filter((d) => d.tipo_publicacao === "AVISO" || !d.tipo_publicacao).length,
          totalResultados: licitacoesFormatadas.filter((d) => d.tipo_publicacao === "RESULTADO").length,
          totalCotacoes: licitacoesFormatadas.filter((d) => d.tipo_publicacao === "COTACAO").length,
          totalValor: licitacoesFormatadas.reduce((acc, curr) => acc + (curr.valor_estimado || 0), 0)
        };

        return NextResponse.json({
          licitacoes: licitacoesFormatadas,
          total: totalRegistros,
          pagina,
          limite,
          placar,
          origem: "supabase"
        });
      }

      if (error) {
        console.warn("Aviso na consulta ao Supabase:", error.message || error);
      }
    } catch (err) {
      console.warn("Aviso ao conectar no Supabase, utilizando base agregada:", err);
    }
  }

  // 2. BASE AGREGADA REAL DO PNCP (Editais coletados via scrapers/pncp_api.py)
  let baseEditais: Licitacao[] = [...DADOS_EXEMPLO];
  try {
    const fs = await import("fs");
    const path = await import("path");
    const backupPath = path.join(process.cwd(), "scrapers", "editais_pncp_backup.json");
    if (fs.existsSync(backupPath)) {
      const conteudo = fs.readFileSync(backupPath, "utf-8");
      const editaisJson = JSON.parse(conteudo);
      if (Array.isArray(editaisJson) && editaisJson.length > 0) {
        baseEditais = editaisJson;
      }
    }
  } catch (errJson) {
    console.warn("Aviso ao ler editais_pncp_backup.json:", errJson);
  }

  let filtrados = [...baseEditais];

  // Filtro obrigatório de Oportunidades Futuras: oculta licitações expiradas
  const dataDeHojeIso = new Date().toISOString();
  filtrados = filtrados.filter((item) => {
    if (!item.data_disputa) return false;
    return item.data_disputa >= dataDeHojeIso;
  });

  if (busca) {
    const listaRadicais = extrairListaRadicais(busca);
    filtrados = filtrados.filter((item) =>
      correspondeRadicais(`${item.objeto} ${item.orgao} ${item.numero_processo || ""}`, listaRadicais)
    );
  }

  if (estadoParam && estadoParam !== "TODOS") {
    filtrados = filtrados.filter((item) => item.estado.toUpperCase() === estadoParam);
  }

  if (municipioParam) {
    filtrados = filtrados.filter((item) =>
      removerAcentos(item.municipio).includes(removerAcentos(municipioParam))
    );
  }

  if (regiaoParam && regiaoParam !== "TODAS") {
    filtrados = filtrados.filter((item) => {
      const regItem = item.regiao || UF_REGIAO_MAP[item.estado] || "Outros";
      return regItem === regiaoParam;
    });
  }

  if (modalidadeParam && modalidadeParam !== "TODAS") {
    filtrados = filtrados.filter((item) => item.modalidade === modalidadeParam);
  }

  if (esferaParam && esferaParam !== "TODAS") {
    filtrados = filtrados.filter((item) => item.esfera === esferaParam);
  }

  if (tipoPublicacao && tipoPublicacao !== "TODOS") {
    filtrados = filtrados.filter((item) => item.tipo_publicacao === tipoPublicacao);
  }

  if (valorMin !== null && !isNaN(valorMin)) {
    filtrados = filtrados.filter((item) => (item.valor_estimado || 0) >= valorMin);
  }
  if (valorMax !== null && !isNaN(valorMax)) {
    filtrados = filtrados.filter((item) => (item.valor_estimado || 0) <= valorMax);
  }

  if (fonte && fonte !== "TODOS") {
    filtrados = filtrados.filter((item) => item.fonte === fonte);
  }

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
    return new Date(a.data_disputa || 0).getTime() - new Date(b.data_disputa || 0).getTime();
  });

  const placar: PlacarDoDia = {
    totalLicitacoes: filtrados.filter((d) => d.tipo_publicacao === "AVISO" || !d.tipo_publicacao).length,
    totalResultados: filtrados.filter((d) => d.tipo_publicacao === "RESULTADO").length,
    totalCotacoes: filtrados.filter((d) => d.tipo_publicacao === "COTACAO").length,
    totalValor: filtrados.reduce((acc, curr) => acc + (curr.valor_estimado || 0), 0)
  };

  return NextResponse.json({
    licitacoes: filtrados,
    total: filtrados.length,
    pagina: 1,
    limite: filtrados.length,
    placar,
    origem: "demonstracao"
  });
}
