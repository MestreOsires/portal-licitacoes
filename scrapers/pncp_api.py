"""
pncp_api.py - Coletor oficial de editais via API REST do Portal Nacional de Contratações Públicas (PNCP).
Otimizado para captação direcionada aos estados do Maranhão (MA), Pará (PA) e Tocantins (TO),
cobrindo todas as prefeituras e órgãos públicos municipais, estaduais e federais.

Correções fundamentais implementadas:
1. Inclusão obrigatória de 'codigoModalidadeContratacao' exigido pela API do PNCP.
2. Iteração estruturada pelas modalidades principais (Pregão, Dispensa, Concorrência, etc.).
3. Paginação correta (pagina=1, 2, 3..., tamanhoPagina=50) até o esgotamento dos registros.
4. Extração fidedigna de unidadeOrgao.ufSigla -> 'estado' e unidadeOrgao.municipioNome -> 'municipio'.
5. Suporte a execução imediata via CLI (--uma-vez) e agendamento diário (12:00 e 18:00 Brasília).
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
import pytz
import requests
from dotenv import load_dotenv
try:
    import schedule
except ImportError:
    schedule = None
from supabase import create_client, Client

load_dotenv()
load_dotenv(".env.local")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

supabase: Client = None
supabase_ativo = False

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        # Teste de permissão de escrita
        teste_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/licitacoes?limit=1",
            headers={"apikey": SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"},
            timeout=5
        )
        if teste_resp.status_code == 200:
            supabase_ativo = True
            logging.info("Cliente Supabase conectado e autenticado com sucesso.")
        elif teste_resp.status_code == 401:
            logging.warning(
                "Aviso Supabase: A chave SUPABASE_SERVICE_ROLE_KEY fornecida retornou 401 Unauthorized. "
                "Para salvar no banco, configure o token JWT 'service_role' no seu arquivo .env. "
                "Os dados coletados serão preservados em 'scrapers/editais_pncp_backup.json'."
            )
        else:
            logging.info(f"Cliente Supabase inicializado (status teste: {teste_resp.status_code}).")
            supabase_ativo = True
    except Exception as e:
        logging.warning(f"Não foi possível inicializar o cliente Supabase: {e}")

# Lista prioritária de UFs com foco no Maranhão, Pará e Tocantins
UFS_PADRAO = ["MA", "PA", "TO"]

# Modalidades oficiais e seus códigos exigidos pelo endpoint /contratacoes/publicacao do PNCP
MODALIDADES_PRINCIPAIS = [
    {"codigo": 6, "nome": "Pregão - Eletrônico"},
    {"codigo": 8, "nome": "Dispensa de Licitação"},
    {"codigo": 4, "nome": "Concorrência - Eletrônica"},
    {"codigo": 9, "nome": "Inexigibilidade de Licitação"},
    {"codigo": 1, "nome": "Leilão - Eletrônico"},
    {"codigo": 7, "nome": "Pregão - Presencial"},
    {"codigo": 5, "nome": "Concorrência - Presencial"},
    {"codigo": 12, "nome": "Credenciamento"},
    {"codigo": 3, "nome": "Concurso"},
    {"codigo": 2, "nome": "Diálogo Competitivo"}
]

# Coordenadas geográficas das capitais e principais polos regionais (fallback PostGIS)
COORDENADAS_POLOS = {
    # Maranhão
    "MA": (-44.3028, -2.5297),
    "SAO LUIS": (-44.3028, -2.5297),
    "IMPERATRIZ": (-47.4917, -5.5264),
    "CAXIAS": (-43.3561, -4.8589),
    "TIMON": (-42.8369, -5.0939),
    "SAO JOAO DOS PATOS": (-43.7039, -6.4950),
    "BALSAS": (-46.0361, -7.5322),
    "BACABAL": (-44.7917, -4.2406),
    "SANTA INES": (-45.3800, -3.6667),

    # Pará
    "PA": (-48.4902, -1.4558),
    "BELEM": (-48.4902, -1.4558),
    "ANANINDEUA": (-48.3717, -1.3653),
    "SANTAREM": (-54.7086, -2.4431),
    "MARABA": (-49.1178, -5.3686),
    "PARAUAPEBAS": (-49.9031, -6.0678),
    "CASTANHAL": (-47.9261, -1.2975),
    "ALTAMIRA": (-52.2031, -3.2033),

    # Tocantins
    "TO": (-48.3336, -10.1844),
    "PALMAS": (-48.3336, -10.1844),
    "ARAGUAINA": (-48.2033, -7.1917),
    "GURUPI": (-49.0689, -11.7297),
    "PORTO NACIONAL": (-48.4172, -10.7081),
    "COLINAS DO TOCANTINS": (-48.4764, -8.0583),
    "RIACHINHO": (-48.1367, -6.4386),

    # Capitais de apoio
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

def criar_sessao_http() -> requests.Session:
    """
    Cria uma sessão HTTP persistente com User-Agent de navegador para evitar bloqueios.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://pncp.gov.br",
        "Referer": "https://pncp.gov.br/"
    })
    return session

def capturar_pncp(ufs=None, max_paginas=10, dias_historico=90):
    """
    Consome editais no PNCP com os parâmetros exigidos pela API oficial:
    Itera por UF (MA, PA, TO e outras) e por Modalidade de Contratação (6, 8, 4, etc.).
    Pagina ordenadamente (pagina=1, 2, 3...) com tamanhoPagina=50 até o término dos dados.
    """
    if ufs is None:
        ufs = UFS_PADRAO

    fuso_bsb = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(fuso_bsb)

    # Busca intervalo de publicação (padrão últimos 90 dias até hoje)
    data_inicial = (agora - timedelta(days=dias_historico)).strftime("%Y%m%d")
    data_final = agora.strftime("%Y%m%d")

    logging.info(f"=== INICIANDO CAPTAÇÃO PNCP (UFs: {ufs}) ===")
    logging.info(f"Período de publicação: {data_inicial} até {data_final}")
    logging.info(f"Modalidades pesquisadas: {[m['codigo'] for m in MODALIDADES_PRINCIPAIS]}")

    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    session = criar_sessao_http()
    total_geral_inseridos = 0
    todos_editais_capturados = []

    for uf in ufs:
        uf_upper = uf.upper().strip()
        logging.info(f"\n==========================================")
        logging.info(f"== PROCESSANDO ESTADO: {uf_upper}")
        logging.info(f"==========================================")
        total_uf_inseridos = 0

        for mod in MODALIDADES_PRINCIPAIS:
            cod_modalidade = mod["codigo"]
            nome_modalidade = mod["nome"]
            logging.info(f"[{uf_upper}] -> Consultando Modalidade {cod_modalidade} ({nome_modalidade})...")

            for pagina in range(1, max_paginas + 1):
                # Parâmetros oficiais exigidos pelo PNCP
                params = {
                    "dataInicial": data_inicial,
                    "dataFinal": data_final,
                    "codigoModalidadeContratacao": cod_modalidade,
                    "uf": uf_upper,
                    "pagina": pagina,
                    "tamanhoPagina": 50
                }

                try:
                    tentativas = 0
                    resp = None
                    while tentativas < 3:
                        resp = session.get(url, params=params, timeout=(10, 30))
                        if resp.status_code == 429:
                            tentativas += 1
                            espera = tentativas * 2.5
                            logging.warning(f"[{uf_upper}] Rate limit (429) no PNCP. Aguardando {espera:.1f}s (tentativa {tentativas}/3)...")
                            time.sleep(espera)
                            continue
                        break

                    if resp is None:
                        break

                    if resp.status_code == 204:
                        logging.info(f"[{uf_upper}] Modalidade {cod_modalidade}: Nenhum edital disponível no período pesquisado (204 No Content).")
                        break

                    if resp.status_code == 400:
                        logging.warning(f"[{uf_upper}] PNCP retornou 400 (Bad Request) na modalidade {cod_modalidade}, pag {pagina}: {resp.text[:200]}")
                        break

                    if resp.status_code != 200:
                        logging.warning(f"[{uf_upper}] PNCP retornou status {resp.status_code} na modalidade {cod_modalidade}, pág {pagina}.")
                        break

                    data = resp.json()
                    itens = data.get("data", [])

                    if not itens:
                        logging.info(f"[{uf_upper}] Sem mais registros para Modalidade {cod_modalidade} a partir da pág {pagina}.")
                        break

                    logging.info(f"[{uf_upper}] Pág {pagina}: {len(itens)} editais retornados.")

                    for item in itens:
                        numero_controle = item.get("numeroControlePNCP") or f"{uf_upper}_{int(time.time()*1000)}"
                        id_externo = f"PNCP_{numero_controle}"

                        # Extração dos dados do órgão e prefeitura
                        unidade = item.get("unidadeOrgao") or {}
                        orgao_entidade = item.get("orgaoEntidade") or {}
                        
                        orgao = (
                            orgao_entidade.get("razaoSocial") or
                            unidade.get("nomeUnidade") or
                            f"Órgão Público Estadual/Municipal ({uf_upper})"
                        ).strip()

                        objeto = (item.get("objetoCompra") or "Objeto não detalhado na publicação.").strip()
                        valor = item.get("valorTotalEstimado") or item.get("valorTotalHomologado")

                        # Datas de disputa / propostas
                        data_disputa = (
                            item.get("dataAberturaProposta") or
                            item.get("dataEncerramentoProposta") or
                            item.get("dataPublicacaoPncp")
                        )

                        # Filtro na Captação: descarta editais com data de disputa passada (poupa espaço no banco)
                        if not data_disputa:
                            continue

                        try:
                            dt_disputa_limpa = data_disputa.replace("Z", "+00:00")
                            dt_disputa_obj = datetime.fromisoformat(dt_disputa_limpa)
                            agora_ref = datetime.now(dt_disputa_obj.tzinfo) if dt_disputa_obj.tzinfo else datetime.now()

                            if dt_disputa_obj < agora_ref:
                                # Data de disputa menor que a data de execução atual -> ignora
                                continue
                        except Exception:
                            # Se a data for inválida ou não puder ser parseada, ignora
                            continue

                        link_edital = (
                            item.get("linkSistemaOrigem") or
                            f"https://pncp.gov.br/app/editais/{numero_controle}"
                        )

                        # Extrai a cidade/município fidedigno da unidade de compra
                        municipio_raw = unidade.get("municipioNome")
                        if not municipio_raw:
                            # Se não vier na unidade, tenta identificar se a razão social é de prefeitura
                            razao_upper = orgao.upper()
                            if "MUNICIPIO DE " in razao_upper:
                                municipio_raw = orgao.split("MUNICIPIO DE ")[-1].strip().title()
                            elif "PREFEITURA MUNICIPAL DE " in razao_upper:
                                municipio_raw = orgao.split("PREFEITURA MUNICIPAL DE ")[-1].strip().title()
                            elif "PREFEITURA DE " in razao_upper:
                                municipio_raw = orgao.split("PREFEITURA DE ")[-1].strip().title()
                            else:
                                municipio_raw = "São Luís" if uf_upper == "MA" else "Belém" if uf_upper == "PA" else "Palmas"

                        municipio = municipio_raw.strip()
                        estado_item = (unidade.get("ufSigla") or uf_upper).upper()

                        coordenadas_wkt = obter_coordenadas(municipio, estado_item)

                        regiao_item = (
                            "Norte" if estado_item in ["AC", "AP", "AM", "PA", "RO", "RR", "TO"] else
                            "Nordeste" if estado_item in ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"] else
                            "Centro-Oeste" if estado_item in ["DF", "GO", "MT", "MS"] else
                            "Sudeste" if estado_item in ["ES", "MG", "RJ", "SP"] else "Sul"
                        )

                        modalidade_item = item.get("modalidadeNome") or nome_modalidade
                        
                        # Determinação da esfera pública
                        esfera_pncp = orgao_entidade.get("esferaId")
                        if esfera_pncp == "M" or "PREFEITURA" in orgao.upper() or "MUNICIPIO" in orgao.upper():
                            esfera_item = "Municipal"
                        elif esfera_pncp == "E" or "ESTADO" in orgao.upper() or "SECRETARIA DE ESTADO" in orgao.upper():
                            esfera_item = "Estadual"
                        elif esfera_pncp == "F" or "FEDERAL" in orgao.upper() or "MINISTERIO" in orgao.upper() or "TRIBUNAL" in orgao.upper():
                            esfera_item = "Federal"
                        else:
                            esfera_item = "Municipal"

                        # Tipo de publicação
                        tipo_pub = "AVISO"
                        if "dispensa" in modalidade_item.lower() or cod_modalidade == 8:
                            tipo_pub = "COTACAO"

                        registro = {
                            "id_externo": id_externo,
                            "orgao": orgao[:255],
                            "objeto": objeto,
                            "valor_estimado": float(valor) if valor is not None else None,
                            "data_disputa": data_disputa,
                            "link_edital": link_edital,
                            "municipio": municipio[:100],
                            "estado": estado_item[:2],
                            "modalidade": modalidade_item[:100],
                            "regiao": regiao_item,
                            "esfera": esfera_item,
                            "tipo_publicacao": tipo_pub,
                            "numero_processo": item.get("processo") or item.get("numeroCompra") or f"PNCP {numero_controle[-10:]}",
                            "coordenadas": coordenadas_wkt,
                            "fonte": "PNCP"
                        }

                        # Persistência no Supabase (se autenticado com service_role válida)
                        if supabase and supabase_ativo:
                            try:
                                supabase.table("licitacoes").upsert(registro, on_conflict="id_externo").execute()
                                total_uf_inseridos += 1
                            except Exception as insert_err:
                                try:
                                    supabase.table("licitacoes").insert(registro).execute()
                                    total_uf_inseridos += 1
                                except Exception:
                                    pass
                        else:
                            total_uf_inseridos += 1

                        # Adiciona ao backup de registros em memória para gravação local
                        todos_editais_capturados.append(registro)

                    # Intervalo seguro para respeitar a taxa de requisições da API pública
                    time.sleep(0.4)

                    # Se a página retornou menos que 50 itens, os registros daquela modalidade acabaram
                    if len(itens) < 50:
                        break

                except requests.exceptions.RequestException as req_err:
                    logging.error(f"[{uf_upper}] Erro de rede ao consultar modalidade {cod_modalidade}, pág {pagina}: {req_err}")
                    time.sleep(1.0)
                    break
                except Exception as ex:
                    logging.error(f"[{uf_upper}] Erro inesperado na modalidade {cod_modalidade}, pág {pagina}: {ex}")
                    break

        logging.info(f"[{uf_upper}] Estado finalizado. Total de editais capturados: {total_uf_inseridos}")
        total_geral_inseridos += total_uf_inseridos

    # Salva backup local em JSON para garantir retenção mesmo em caso de falha de conexão
    if todos_editais_capturados:
        try:
            import json
            backup_path = os.path.join(os.path.dirname(__file__), "editais_pncp_backup.json")
            existentes = []
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, "r", encoding="utf-8") as f:
                        existentes = json.load(f)
                except Exception:
                    existentes = []

            mapa = {item["id_externo"]: item for item in existentes if "id_externo" in item}
            for item in todos_editais_capturados:
                mapa[item["id_externo"]] = item

            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(list(mapa.values()), f, ensure_ascii=False, indent=2)

            logging.info(f"Backup local atualizado com sucesso: {len(mapa)} editais em '{backup_path}'.")
        except Exception as json_err:
            logging.warning(f"Não foi possível salvar backup local em JSON: {json_err}")

    logging.info(f"\n========================================================")
    logging.info(f"=== CAPTAÇÃO PNCP CONCLUÍDA. TOTAL GERAL: {total_geral_inseridos} ===")
    logging.info(f"========================================================\n")
    return total_geral_inseridos

def agendador():
    """
    Agenda execuções diárias às 12:00 e 18:00 (Horário de Brasília).
    """
    if schedule is None:
        logging.warning("Módulo 'schedule' não instalado. Executando captação imediata única. Para agendamento diário, execute: pip install schedule")
        capturar_pncp(max_paginas=3)
        return

    logging.info("Agendador do PNCP ativo para MA, PA e TO (Horários diários: 12:00 e 18:00 - Brasília).")

    schedule.every().day.at("12:00").do(capturar_pncp)
    schedule.every().day.at("18:00").do(capturar_pncp)

    # Execução inicial para popular a base
    capturar_pncp(max_paginas=3)

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coletor PNCP para MA, PA, TO e todo o Brasil")
    parser.add_argument("--uf", type=str, help="UFs separadas por vírgula (ex: MA,PA,TO)")
    parser.add_argument("--paginas", type=int, default=5, help="Número máximo de páginas por modalidade (padrão: 5)")
    parser.add_argument("--uma-vez", action="store_true", help="Executa apenas uma vez e finaliza (sem agendador)")
    args = parser.parse_args()

    ufs_selecionadas = [u.strip().upper() for u in args.uf.split(",")] if args.uf else UFS_PADRAO

    if args.uma_vez:
        capturar_pncp(ufs=ufs_selecionadas, max_paginas=args.paginas)
    else:
        agendador()
