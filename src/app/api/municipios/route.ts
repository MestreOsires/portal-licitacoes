import { NextResponse } from "next/server";
import { supabase, isSupabaseConfigured } from "@/lib/supabaseClient";
import fs from "fs";
import path from "path";

// Lista de municípios de referência por UF caso o banco esteja em fase de carga inicial
const MUNICIPIOS_REFERENCIA: Record<string, string[]> = {
  MA: [
    "São Luís", "Imperatriz", "São José de Ribamar", "Timon", "Caxias",
    "Codó", "Paço do Lumiar", "Açailândia", "Bacabal", "Balsas",
    "Santa Inês", "Barra do Corda", "Pinheiro", "Chapadinha", "Santa Luzia",
    "Buriticupu", "Grajaú", "Itapecuru Mirim", "Coroatá", "São João dos Patos",
    "Raposa", "Pedreiras", "Peritoró", "Serrano do Maranhão"
  ],
  PA: [
    "Belém", "Ananindeua", "Santarém", "Marabá", "Parauapebas",
    "Castanhal", "Abaetetuba", "Cametá", "Marituba", "Bragança",
    "São Félix do Xingu", "Barcarena", "Altamira", "Tucuruí", "Paragominas",
    "Tailândia", "Breves", "Itaituba", "Redenção", "Moju", "Capanema", "Xinguara"
  ],
  TO: [
    "Palmas", "Araguaína", "Gurupi", "Porto Nacional", "Paraíso do Tocantins",
    "Colinas do Tocantins", "Guaraí", "Tocantinópolis", "Dianópolis", "Miracema do Tocantins",
    "Formoso do Araguaia", "Taguatinga", "Augustinópolis", "Pedro Afonso", "Riachinho",
    "Palmeirante", "Aurora do Tocantins", "Ipueiras", "Peixe", "Natividade", "Campos Lindos"
  ],
  SP: ["São Paulo", "Campinas", "Guarulhos", "São Bernardo do Campo", "Santo André", "Osasco", "Sorocaba", "Ribeirão Preto"],
  RJ: ["Rio de Janeiro", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu", "Niterói", "Campos dos Goytacazes"],
  MG: ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros", "Uberaba"],
  DF: ["Brasília"]
};

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const ufParam = (searchParams.get("uf") || "").toUpperCase().trim();

  if (!ufParam) {
    return NextResponse.json({ municipios: [] });
  }

  // 1. Tenta buscar municípios únicos no Supabase
  if (isSupabaseConfigured && supabase) {
    try {
      const dataDeHoje = new Date().toISOString();
      let { data, error } = await supabase
        .from("licitacoes")
        .select("municipio")
        .eq("estado", ufParam)
        .gte("data_disputa", dataDeHoje)
        .not("municipio", "is", null)
        .limit(1000);

      // Fallback resiliente se a coluna for 'uf'
      if (error && (error.message?.includes("estado") || error.code === "PGRST204")) {
        const retryUf = await supabase
          .from("licitacoes")
          .select("municipio")
          .eq("uf", ufParam)
          .gte("data_disputa", dataDeHoje)
          .not("municipio", "is", null)
          .limit(1000);
        data = retryUf.data;
        error = retryUf.error;
      }

      if (!error && data && data.length > 0) {
        const cidadesSet = new Set<string>();
        for (const item of data as Array<{ municipio?: string; cidade?: string }>) {
          const nome = (item.municipio || item.cidade || "").trim();
          if (nome && nome.length > 1) {
            cidadesSet.add(nome);
          }
        }

        const municipiosBanco = Array.from(cidadesSet).sort((a, b) =>
          a.localeCompare(b, "pt-BR", { sensitivity: "base" })
        );

        if (municipiosBanco.length > 0) {
          return NextResponse.json({
            municipios: municipiosBanco,
            origem: "supabase",
            total: municipiosBanco.length
          });
        }
      }
    } catch (err) {
      console.warn("Aviso ao buscar municípios no Supabase:", err);
    }
  }

  // 2. Busca nos editais coletados do PNCP (scrapers/editais_pncp_backup.json)
  try {
    const backupPath = path.join(process.cwd(), "scrapers", "editais_pncp_backup.json");
    if (fs.existsSync(backupPath)) {
      const conteudo = fs.readFileSync(backupPath, "utf-8");
      const editaisJson = JSON.parse(conteudo);
      const cidadesSet = new Set<string>();

      for (const edital of editaisJson) {
        if (edital.estado === ufParam && edital.municipio) {
          cidadesSet.add(edital.municipio.trim());
        }
      }

      if (cidadesSet.size > 0) {
        const cidadesOrdenadas = Array.from(cidadesSet).sort((a, b) =>
          a.localeCompare(b, "pt-BR", { sensitivity: "base" })
        );
        return NextResponse.json({
          municipios: cidadesOrdenadas,
          origem: "pncp_local",
          total: cidadesOrdenadas.length
        });
      }
    }
  } catch (errJson) {
    console.warn("Aviso ao ler backup PNCP para municípios:", errJson);
  }

  // 3. Fallback de referência
  const fallbackList = MUNICIPIOS_REFERENCIA[ufParam] || [];
  return NextResponse.json({
    municipios: fallbackList,
    origem: "referencia",
    total: fallbackList.length
  });
}
