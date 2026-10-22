/**
 * searchUtils.ts - Algoritmos de busca e normalização reversos do Universo Licitações.
 * Implementa normalização por radical (Stemming em português sem acentos e sem plural),
 * detecção de macrorregiões e filtros cronológicos de agenda de disputa.
 */

export const UF_REGIAO_MAP: Record<string, string> = {
  AC: "Norte",
  AP: "Norte",
  AM: "Norte",
  PA: "Norte",
  RO: "Norte",
  RR: "Norte",
  TO: "Norte",
  AL: "Nordeste",
  BA: "Nordeste",
  CE: "Nordeste",
  MA: "Nordeste",
  PB: "Nordeste",
  PE: "Nordeste",
  PI: "Nordeste",
  RN: "Nordeste",
  SE: "Nordeste",
  DF: "Centro-Oeste",
  GO: "Centro-Oeste",
  MT: "Centro-Oeste",
  MS: "Centro-Oeste",
  ES: "Sudeste",
  MG: "Sudeste",
  RJ: "Sudeste",
  SP: "Sudeste",
  PR: "Sul",
  RS: "Sul",
  SC: "Sul"
};

/**
 * Remove acentuação e converte para minúsculas.
 */
export function removerAcentos(texto: string): string {
  if (!texto) return "";
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

/**
 * Extrai o radical simplificado de uma palavra (inspirado no padrão do Universo Licitações,
 * que elimina variações de singular/plural e sufixos comuns no vocabulário público).
 */
export function extrairRadical(palavra: string): string {
  let p = removerAcentos(palavra);
  if (p.length <= 3) return p;

  // Sufixos comuns em editais de compras públicas
  if (p.endsWith("coes") || p.endsWith("cao")) {
    return p.slice(0, -3); // pavimentacao -> paviment
  }
  if (p.endsWith("amentos") || p.endsWith("amento")) {
    return p.slice(0, -5); // medicamento -> medic
  }
  if (p.endsWith("ores") || p.endsWith("or")) {
    return p.slice(0, -2); // respirador -> respirad
  }
  if (p.endsWith("ens") || p.endsWith("em")) {
    return p.slice(0, -2); // veiculos / veiculo
  }
  if (p.endsWith("eis") || p.endsWith("el")) {
    return p.slice(0, -2);
  }
  if (p.endsWith("as") || p.endsWith("os") || p.endsWith("es") || p.endsWith("is")) {
    return p.slice(0, -1); // computadores -> computadore
  }
  if (p.endsWith("s")) {
    return p.slice(0, -1);
  }

  return p;
}

/**
 * Divide uma consulta de busca (que pode conter vírgulas ou múltiplos termos)
 * em uma lista de radicais normalizados.
 */
export function extrairListaRadicais(consulta: string): string[] {
  if (!consulta) return [];
  // Divide por vírgulas ou espaços múltiplos
  const termos = consulta
    .split(/[,;\n]+/)
    .map((t) => t.trim())
    .filter(Boolean);

  const radicais: string[] = [];

  for (const termo of termos) {
    const palavras = termo.split(/\s+/).filter((w) => w.length > 2);
    for (const w of palavras) {
      const rad = extrairRadical(w);
      if (rad && !radicais.includes(rad)) {
        radicais.push(rad);
      }
    }
  }

  return radicais;
}

/**
 * Testa se um texto (objeto ou órgão do edital) contém os radicais pesquisados.
 */
export function correspondeRadicais(textoAlvo: string, radicais: string[]): boolean {
  if (!radicais || radicais.length === 0) return true;
  const textoLimpo = removerAcentos(textoAlvo);

  // Verifica se pelo menos um dos radicais pesquisados está presente no texto
  return radicais.some((rad) => textoLimpo.includes(rad));
}
