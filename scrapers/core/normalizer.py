"""
scrapers/core/normalizer.py - Normalização geográfica e cadastral rigorosa.
Centraliza as regras para todos os 27 estados e municípios do Brasil.
"""

import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, Dict, Any

FUSO_BSB = ZoneInfo("America/Sao_Paulo")

# Mapeamento oficial de todas as 27 Unidades Federativas do Brasil
UF_INFO: Dict[str, Dict[str, Any]] = {
    "AC": {"nome": "Acre", "regiao": "Norte", "capital": "Rio Branco", "lat": -9.9754, "lng": -67.8249},
    "AL": {"nome": "Alagoas", "regiao": "Nordeste", "capital": "Maceió", "lat": -9.6658, "lng": -35.7351},
    "AP": {"nome": "Amapá", "regiao": "Norte", "capital": "Macapá", "lat": 0.0355, "lng": -51.0705},
    "AM": {"nome": "Amazonas", "regiao": "Norte", "capital": "Manaus", "lat": -3.1190, "lng": -60.0217},
    "BA": {"nome": "Bahia", "regiao": "Nordeste", "capital": "Salvador", "lat": -12.9714, "lng": -38.5014},
    "CE": {"nome": "Ceará", "regiao": "Nordeste", "capital": "Fortaleza", "lat": -3.7327, "lng": -38.5270},
    "DF": {"nome": "Distrito Federal", "regiao": "Centro-Oeste", "capital": "Brasília", "lat": -15.7975, "lng": -47.8919},
    "ES": {"nome": "Espírito Santo", "regiao": "Sudeste", "capital": "Vitória", "lat": -20.3155, "lng": -40.3128},
    "GO": {"nome": "Goiás", "regiao": "Centro-Oeste", "capital": "Goiânia", "lat": -16.6869, "lng": -49.2648},
    "MA": {"nome": "Maranhão", "regiao": "Nordeste", "capital": "São Luís", "lat": -2.5307, "lng": -44.3068},
    "MT": {"nome": "Mato Grosso", "regiao": "Centro-Oeste", "capital": "Cuiabá", "lat": -15.6014, "lng": -56.0979},
    "MS": {"nome": "Mato Grosso do Sul", "regiao": "Centro-Oeste", "capital": "Campo Grande", "lat": -20.4697, "lng": -54.6201},
    "MG": {"nome": "Minas Gerais", "regiao": "Sudeste", "capital": "Belo Horizonte", "lat": -19.9245, "lng": -43.9352},
    "PA": {"nome": "Pará", "regiao": "Norte", "capital": "Belém", "lat": -1.4558, "lng": -48.4902},
    "PB": {"nome": "Paraíba", "regiao": "Nordeste", "capital": "João Pessoa", "lat": -7.1195, "lng": -34.8450},
    "PR": {"nome": "Paraná", "regiao": "Sul", "capital": "Curitiba", "lat": -25.4284, "lng": -49.2733},
    "PE": {"nome": "Pernambuco", "regiao": "Nordeste", "capital": "Recife", "lat": -8.0476, "lng": -34.8770},
    "PI": {"nome": "Piauí", "regiao": "Nordeste", "capital": "Teresina", "lat": -5.0920, "lng": -42.8038},
    "RJ": {"nome": "Rio de Janeiro", "regiao": "Sudeste", "capital": "Rio de Janeiro", "lat": -22.9068, "lng": -43.1729},
    "RN": {"nome": "Rio Grande do Norte", "regiao": "Nordeste", "capital": "Natal", "lat": -5.7945, "lng": -35.2110},
    "RS": {"nome": "Rio Grande do Sul", "regiao": "Sul", "capital": "Porto Alegre", "lat": -30.0346, "lng": -51.2177},
    "RO": {"nome": "Rondônia", "regiao": "Norte", "capital": "Porto Velho", "lat": -8.7612, "lng": -63.9039},
    "RR": {"nome": "Roraima", "regiao": "Norte", "capital": "Boa Vista", "lat": 2.8235, "lng": -60.6758},
    "SC": {"nome": "Santa Catarina", "regiao": "Sul", "capital": "Florianópolis", "lat": -27.5954, "lng": -48.5480},
    "SP": {"nome": "São Paulo", "regiao": "Sudeste", "capital": "São Paulo", "lat": -23.5505, "lng": -46.6333},
    "SE": {"nome": "Sergipe", "regiao": "Nordeste", "capital": "Aracaju", "lat": -10.9472, "lng": -37.0731},
    "TO": {"nome": "Tocantins", "regiao": "Norte", "capital": "Palmas", "lat": -10.1844, "lng": -48.3336}
}

TODAS_UFS = list(UF_INFO.keys())

def remover_acentos(texto: str) -> str:
    """Remove marcas diacríticas mantendo caracteres ASCII padrão."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")

def normalizar_uf(uf_candidata: Optional[str]) -> str:
    """Valida e retorna a sigla da UF oficial em caixa alta (ou 'DF' se indefinido)."""
    if not uf_candidata:
        return "DF"
    sigla = uf_candidata.strip().upper()[:2]
    return sigla if sigla in UF_INFO else "DF"

def deduzir_regiao(uf: str) -> str:
    """Retorna a Macrorregião geográfica correspondente à UF."""
    sigla = normalizar_uf(uf)
    return UF_INFO.get(sigla, {}).get("regiao", "Outros")

def capital_da_uf(uf: str) -> str:
    """Retorna o nome oficial da capital da UF."""
    sigla = normalizar_uf(uf)
    return UF_INFO.get(sigla, {}).get("capital", "Brasília")

def obter_coordenadas(municipio: str, uf: str) -> str:
    """Gera representação WKT POINT(lng lat) para PostGIS."""
    sigla = normalizar_uf(uf)
    info = UF_INFO.get(sigla)
    if info:
        return f"POINT({info['lng']} {info['lat']})"
    return "POINT(-47.8919 -15.7975)"

def deduzir_municipio(orgao: str, uf: str, municipio_candidato: Optional[str] = None) -> str:
    """
    Higieniza e normaliza o nome do município. Se for órgão estadual ou indefinido,
    associa com segurança à Capital do Estado.
    """
    if municipio_candidato and len(municipio_candidato.strip()) > 2:
        m_limpo = municipio_candidato.strip().title()
        # Remove sufixos como '- MA', '/TO', etc.
        m_limpo = re.sub(r'[\s\-\/]+[A-Z]{2}$', '', m_limpo).strip()
        return m_limpo

    orgao_up = (orgao or "").upper()
    # Verifica padrões comuns de prefeituras
    for padrao in [
        r'PREFEITURA MUNICIPAL DE\s+([A-ZÀ-Ú\s\']+)',
        r'PREFEITURA DE\s+([A-ZÀ-Ú\s\']+)',
        r'MUNIC[IÍ]PIO DE\s+([A-ZÀ-Ú\s\']+)',
        r'C[AÂ]MARA MUNICIPAL DE\s+([A-ZÀ-Ú\s\']+)'
    ]:
        m = re.search(padrao, orgao_up)
        if m:
            nome_cid = m.group(1).split("-")[0].split("/")[0].strip().title()
            if len(nome_cid) > 2:
                return nome_cid

    # Se for órgão da administração estadual direta/indireta, assume a capital
    return capital_da_uf(uf)

def deduzir_esfera(orgao: str) -> str:
    """Determina se a esfera é Federal, Estadual ou Municipal."""
    org_up = (orgao or "").upper()
    if any(k in org_up for k in ["PREFEITURA", "MUNICÍPIO", "MUNICIPIO", "CÂMARA MUNICIPAL", "CAMARA MUNICIPAL", "FUNDO MUNICIPAL", "SEMED", "SEMUS"]):
        return "Municipal"
    if any(k in org_up for k in ["ESTADO", "SECRETARIA DE ESTADO", "GOVERNO DO ESTADO", "DEPARTAMENTO ESTADUAL", "POLICIA MILITAR", "UEMA", "EMAP", "CAEMA", "DETRAN", "SEDUC", "SESA", "SESAP"]):
        return "Estadual"
    if any(k in org_up for k in ["MINISTERIO", "MINISTÉRIO", "FEDERAL", "TRIBUNAL REGIONAL", "UNIVERSIDADE FEDERAL", "IFMA", "DNIT", "INSS", "IBAMA"]):
        return "Federal"
    return "Municipal"

def deduzir_modalidade(texto_modalidade: Optional[str]) -> str:
    """Padroniza a modalidade de licitação com base na nova Lei 14.133/2021."""
    if not texto_modalidade:
        return "Pregão Eletrônico"
    mod_up = texto_modalidade.upper()
    if "DISPENSA" in mod_up or "COTAÇÃO" in mod_up or "COTACAO" in mod_up:
        return "Dispensa Eletrônica"
    if "CONCORRÊNCIA" in mod_up or "CONCORRENCIA" in mod_up:
        return "Concorrência Eletrônica"
    if "INEXIGIBILIDADE" in mod_up:
        return "Inexigibilidade"
    if "PREGÃO PRESENCIAL" in mod_up or "PREGAO PRESENCIAL" in mod_up:
        return "Pregão Presencial"
    if "PREGÃO" in mod_up or "PREGAO" in mod_up:
        return "Pregão Eletrônico"
    if "LEILÃO" in mod_up or "LEILAO" in mod_up:
        return "Leilão"
    if "CHAMAMENTO" in mod_up:
        return "Chamamento Público"
    if "CREDENCIAMENTO" in mod_up:
        return "Credenciamento"
    return "Pregão Eletrônico"

def validar_oportunidade_futura(data_disputa_iso: Optional[str]) -> Tuple[bool, Optional[datetime]]:
    """
    REGRA CRÍTICA DE OURO:
    Apenas oportunidades futuras (data_disputa >= agora) são aceitas.
    Retorna (eh_valida, datetime_obj).
    """
    if not data_disputa_iso:
        return False, None

    try:
        dt_limpa = data_disputa_iso.replace("Z", "+00:00")
        dt_obj = datetime.fromisoformat(dt_limpa)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=FUSO_BSB)

        agora = datetime.now(FUSO_BSB)
        if dt_obj >= agora:
            return True, dt_obj
        return False, dt_obj
    except Exception:
        return False, None
