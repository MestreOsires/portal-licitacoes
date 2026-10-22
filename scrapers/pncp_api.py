"""
pncp_api.py - Coletor de editais via API REST do Portal Nacional de Contratações Públicas (PNCP).
Otimizado para captação direcionada aos estados do Maranhão (MA), Pará (PA) e Tocantins (TO).
Itera por páginas garantindo a captação de editais recentes e em aberto.
Agendado para rodar diariamente às 12:00 e 18:00 (Horário de Brasília).
"""

import os
import time
import logging
from datetime import datetime, timedelta
import pytz
import requests
import schedule
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logging.warning("Atenção: Variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY não encontradas no .env.")

supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Lista prioritária de UFs solicitadas
UFS_ALVO = ["MA", "PA", "TO"]
PAGINAS_POR_UF = 5  # Pelo menos as primeiras 5 páginas por estado

# Coordenadas geográficas das capitais e principais polos (fallback PostGIS)
COORDENADAS_POLOS = {
    # Maranhão
    "MA": (-44.3028, -2.5297),  # São Luís
    "SAO LUIS": (-44.3028, -2.5297),
    "IMPERATRIZ": (-47.4917, -5.5264),
    "CAXIAS": (-43.3561, -4.8589),
    
    # Pará
    "PA": (-48.4902, -1.4558),  # Belém
    "BELEM": (-48.4902, -1.4558),
    "ANANINDEUA": (-48.3717, -1.3653),
    "SANTAREM": (-54.7086, -2.4431),
    "MARABA": (-49.1178, -5.3686),
    
    # Tocantins
    "TO": (-48.3336, -10.1844), # Palmas
    "PALMAS": (-48.3336, -10.1844),
    "ARAGUAINA": (-48.2033, -7.1917),
    "GURUPI": (-49.0689, -11.7297),
    
    # Outras capitais de apoio
    "DF": (-47.9292, -15.7801),
    "SP": (-46.6333, -23.5505),
    "RJ": (-43.1729, -22.9068),
    "MG": (-43.9378, -19.9208),
    "BA": (-38.5108, -12.9714),
    "PR": (-49.2731, -25.4284),
    "RS": (-51.2177, -30.0346)
}

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).upper().strip()

def obter_coordenadas(municipio: str, uf: str) -> str:
    """
    Retorna ponto WKT 'POINT(longitude latitude)' para o campo PostGIS.
    """
    muni_norm = normalizar_texto(municipio)
    uf_norm = (uf or "").upper().strip()

    if muni_norm in COORDENADAS_POLOS:
        lng, lat = COORDENADAS_POLOS[muni_norm]
        return f"POINT({lng} {lat})"

    if uf_norm in COORDENADAS_POLOS:
        lng, lat = COORDENADAS_POLOS[uf_norm]
        return f"POINT({lng} {lat})"

    # Fallback padrão Brasília
    return "POINT(-47.9292 -15.7801)"

def capturar_pncp():
    """
    Consome editais no PNCP iterando sobre a lista específica de UFs (MA, PA, TO),
    percorrendo pelo menos as primeiras 5 páginas de cada estado para não perder
    editais vigentes com disputa futura ou recém-publicados.
    """
    fuso_bsb = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(fuso_bsb)
    
    # Busca um intervalo amplo (últimos 90 dias até hoje) para abranger editais abertos
    data_inicial = (agora - timedelta(days=90)).strftime("%Y%m%d")
    data_final = agora.strftime("%Y%m%d")

    logging.info(f"=== INICIANDO CAPTAÇÃO PNCP (Foco: {UFS_ALVO}) ===")
    logging.info(f"Período de publicação pesquisado: {data_inicial} até {data_final}")

    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    total_geral_inseridos = 0

    for uf in UFS_ALVO:
        logging.info(f"--- Processando Estado: {uf} (Mínimo de {PAGINAS_POR_UF} páginas) ---")
        total_uf_inseridos = 0

        for pagina in range(1, PAGINAS_POR_UF + 1):
            params = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "uf": uf,
                "pagina": pagina,
                "tamanhoPagina": 50
            }

            try:
                logging.info(f"[{uf}] Solicitando página {pagina}/{PAGINAS_POR_UF}...")
                response = requests.get(url, params=params, timeout=30)

                if response.status_code != 200:
                    logging.warning(f"[{uf}] PNCP retornou status {response.status_code} na página {pagina}.")
                    break

                data = response.json()
                itens = data.get("data", [])

                if not itens:
                    logging.info(f"[{uf}] Nenhum registro adicional encontrado na página {pagina}.")
                    break

                for item in itens:
                    numero_controle = item.get("numeroControlePNCP") or f"{uf}_{int(time.time()*1000)}"
                    id_externo = f"PNCP_{numero_controle}"
                    
                    orgao = item.get("orgaoEntidade", {}).get("razaoSocial") or f"Órgão Público Estadual/Municipal ({uf})"
                    objeto = item.get("objetoCompra") or "Objeto não detalhado na publicação."
                    valor = item.get("valorTotalEstimado")
                    
                    # Data da disputa ou data de publicação
                    data_disputa = (
                        item.get("dataAberturaProposta") or
                        item.get("dataEncerramentoProposta") or
                        item.get("dataPublicacaoPncp")
                    )
                    
                    link_edital = (
                        item.get("linkSistemaOrigem") or
                        f"https://pncp.gov.br/app/editais/{numero_controle}"
                    )

                    unidade = item.get("unidadeOrgao", {})
                    municipio = unidade.get("municipioNome") or ("São Luís" if uf == "MA" else "Belém" if uf == "PA" else "Palmas")
                    estado_item = (unidade.get("ufSigla") or uf).upper()

                    coordenadas_wkt = obter_coordenadas(municipio, estado_item)

                    regiao_item = (
                        "Norte" if estado_item in ["AC", "AP", "AM", "PA", "RO", "RR", "TO"] else
                        "Nordeste" if estado_item in ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"] else
                        "Centro-Oeste" if estado_item in ["DF", "GO", "MT", "MS"] else
                        "Sudeste" if estado_item in ["ES", "MG", "RJ", "SP"] else "Sul"
                    )
                    modalidade_item = item.get("modalidadeNome") or "Pregão Eletrônico"
                    esfera_item = (
                        "Estadual" if "ESTADO" in orgao.upper() or "SECRETARIA DE ESTADO" in orgao.upper() else
                        "Federal" if "FEDERAL" in orgao.upper() or "MINISTERIO" in orgao.upper() or "TRIBUNAL REGIONAL" in orgao.upper() else
                        "Municipal"
                    )

                    registro = {
                        "id_externo": id_externo,
                        "orgao": orgao[:255],
                        "objeto": objeto,
                        "valor_estimado": float(valor) if valor else None,
                        "data_disputa": data_disputa,
                        "link_edital": link_edital,
                        "municipio": municipio[:100],
                        "estado": estado_item[:2],
                        "modalidade": modalidade_item[:100],
                        "regiao": regiao_item,
                        "esfera": esfera_item,
                        "tipo_publicacao": "AVISO",
                        "numero_processo": item.get("numeroProcesso") or f"PNCP {numero_controle[-10:]}",
                        "coordenadas": coordenadas_wkt,
                        "fonte": "PNCP"
                    }

                    if supabase:
                        try:
                            supabase.table("licitacoes").upsert(registro, on_conflict="id_externo").execute()
                            total_uf_inseridos += 1
                        except Exception as insert_err:
                            logging.error(f"Erro ao salvar edital {id_externo} no Supabase: {insert_err}")
                    else:
                        total_uf_inseridos += 1

                # Intervalo para respeitar a taxa de requisições da API pública
                time.sleep(0.6)

            except Exception as e:
                logging.error(f"[{uf}] Erro ao consultar PNCP na página {pagina}: {e}")
                break

        logging.info(f"[{uf}] Concluído. Total de editais processados para {uf}: {total_uf_inseridos}")
        total_geral_inseridos += total_uf_inseridos

    logging.info(f"=== CAPTAÇÃO PNCP FINALIZADA. TOTAL GERAL INSERIDO: {total_geral_inseridos} ===")

def agendador():
    """
    Agenda execuções diárias às 12:00 e 18:00 (Horário de Brasília).
    """
    logging.info("Agendador do PNCP ativo para MA, PA e TO (Horários: 12:00 e 18:00 - Brasília).")

    schedule.every().day.at("12:00").do(capturar_pncp)
    schedule.every().day.at("18:00").do(capturar_pncp)

    # Execução imediata para alimentar a base
    capturar_pncp()

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    agendador()
