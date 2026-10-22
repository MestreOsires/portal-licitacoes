"""
scrapers/pncp_api.py - Motor de Captação Nacional PNCP (Portal Nacional de Contratações Públicas).
Cobre todos os 27 estados e o Distrito Federal com paginação profunda por data e modalidade.
Aplica estritamente a política de oportunidades futuras (data_disputa >= agora).
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import schedule
from scrapers.core.normalizer import (
    TODAS_UFS,
    normalizar_uf,
    deduzir_regiao,
    deduzir_municipio,
    deduzir_esfera,
    deduzir_modalidade,
    obter_coordenadas,
    validar_oportunidade_futura,
    FUSO_BSB
)
from scrapers.core.database import salvar_licitacoes

# Modalidades oficiais regulamentadas pelo PNCP (Lei 14.133/2021)
MODALIDADES_PNCP = [
    {"codigo": 6, "nome": "Pregão - Eletrônico"},
    {"codigo": 8, "nome": "Dispensa de Licitação"},
    {"codigo": 4, "nome": "Concorrência - Eletrônica"},
    {"codigo": 9, "nome": "Inexigibilidade"},
    {"codigo": 1, "nome": "Leilão - Eletrônico"},
    {"codigo": 13, "nome": "Manifestação de Interesse"},
    {"codigo": 14, "nome": "Pré-qualificação"}
]

def criar_sessao_http() -> requests.Session:
    """Cria uma sessão HTTP persistente com headers de navegador para resiliência de rede."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        "Origin": "https://pncp.gov.br",
        "Referer": "https://pncp.gov.br/"
    })
    return session

def capturar_pncp_uf(
    uf: str,
    data_inicial: str,
    data_final: str,
    session: requests.Session,
    max_paginas: int = 10,
    modalidades: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Realiza a varredura profunda do PNCP para uma UF específica, iterando pelas modalidades.
    """
    uf_upper = normalizar_uf(uf)
    modalidades_alvo = modalidades or MODALIDADES_PNCP
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    editais_uf = []

    logging.info(f"\n[{uf_upper}] Iniciando captação PNCP ({data_inicial} a {data_final})")

    for mod in modalidades_alvo:
        cod_mod = mod["codigo"]
        nome_mod = mod["nome"]

        for pagina in range(1, max_paginas + 1):
            params = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "codigoModalidadeContratacao": cod_mod,
                "uf": uf_upper,
                "pagina": pagina,
                "tamanhoPagina": 50
            }

            try:
                resp = None
                for tentativa in range(1, 4):
                    resp = session.get(url, params=params, timeout=(10, 30))
                    if resp.status_code == 429:
                        espera = tentativa * 2.0
                        logging.warning(f"[{uf_upper}] Rate-limit (429) na modalidade {cod_mod}, aguardando {espera:.1f}s...")
                        time.sleep(espera)
                        continue
                    break

                if resp is None:
                    break

                if resp.status_code == 204:
                    # Sem mais dados no período para esta modalidade
                    break

                if resp.status_code == 400:
                    logging.debug(f"[{uf_upper}] PNCP 400 na modalidade {cod_mod}, pág {pagina}: {resp.text[:100]}")
                    break

                if resp.status_code != 200:
                    logging.warning(f"[{uf_upper}] Status HTTP {resp.status_code} na modalidade {cod_mod}, pág {pagina}")
                    break

                data = resp.json()
                itens = data.get("data", [])
                if not itens:
                    break

                for item in itens:
                    numero_controle = item.get("numeroControlePNCP") or ""
                    id_externo = f"PNCP_{numero_controle}" if numero_controle else f"PNCP_{item.get('id')}"

                    orgao_entidade = item.get("orgaoEntidade") or {}
                    unidade = item.get("unidadeOrgao") or {}

                    orgao_nome = (
                        orgao_entidade.get("razaoSocial") or
                        unidade.get("nomeUnidade") or
                        f"Órgão Público ({uf_upper})"
                    ).strip()

                    objeto = (item.get("objetoCompra") or "Objeto não detalhado na publicação.").strip()
                    valor = item.get("valorTotalEstimado") or item.get("valorTotalHomologado")

                    # Data de disputa / propostas
                    data_disputa = (
                        item.get("dataAberturaProposta") or
                        item.get("dataEncerramentoProposta") or
                        item.get("dataPublicacaoPncp")
                    )

                    # FILTRO ESTRITO DE DATA FUTURA (data_disputa >= agora)
                    eh_futuro, _ = validar_oportunidade_futura(data_disputa)
                    if not eh_futuro:
                        continue

                    # Resolução do Município e Localização
                    municipio_bruto = unidade.get("municipioNome")
                    municipio = deduzir_municipio(orgao_nome, uf_upper, municipio_bruto)
                    coordenadas = obter_coordenadas(municipio, uf_upper)
                    esfera = deduzir_esfera(orgao_nome)
                    modalidade_nome = item.get("modalidadeNome") or nome_mod
                    modalidade = deduzir_modalidade(modalidade_nome)

                    link_edital = (
                        item.get("linkSistemaOrigem") or
                        f"https://pncp.gov.br/app/editais/{numero_controle}"
                    )

                    tipo_pub = "COTACAO" if "dispensa" in modalidade.lower() or cod_mod == 8 else "AVISO"
                    num_processo = item.get("processo") or item.get("numeroCompra") or f"PNCP {numero_controle[-10:]}"

                    registro = {
                        "id_externo": id_externo,
                        "orgao": orgao_nome[:255],
                        "objeto": objeto[:1000],
                        "valor_estimado": float(valor) if valor is not None else None,
                        "data_disputa": data_disputa,
                        "link_edital": link_edital,
                        "municipio": municipio[:100],
                        "estado": uf_upper,
                        "modalidade": modalidade[:100],
                        "regiao": deduzir_regiao(uf_upper),
                        "esfera": esfera,
                        "tipo_publicacao": tipo_pub,
                        "numero_processo": str(num_processo)[:50],
                        "coordenadas": coordenadas,
                        "fonte": "PNCP"
                    }
                    editais_uf.append(registro)

                # Intervalo suave para respeitar a API do PNCP
                time.sleep(0.25)

                # Se a página retornou menos que 50 itens, os registros daquela modalidade acabaram
                if len(itens) < 50:
                    break

            except Exception as err:
                logging.error(f"[{uf_upper}] Erro ao consultar modalidade {cod_mod}, pág {pagina}: {err}")
                break

    logging.info(f"[{uf_upper}] Concluído: {len(editais_uf)} editais futuros capturados no PNCP.")
    return editais_uf

def executar_coleta_pncp_nacional(
    ufs: Optional[List[str]] = None,
    dias_historico: int = 3,
    max_paginas: int = 10,
    salvar_banco: bool = True
) -> List[Dict[str, Any]]:
    """
    Executa a varredura nacional do PNCP em todas as 27 UFs do Brasil (ou UFs filtradas).
    """
    ufs_alvo = [normalizar_uf(u) for u in ufs] if ufs else TODAS_UFS
    agora = datetime.now(FUSO_BSB)

    # Janela de publicação recente (últimos N dias até hoje)
    data_inicial = (agora - timedelta(days=dias_historico)).strftime("%Y%m%d")
    data_final = agora.strftime("%Y%m%d")

    logging.info(f"\n=======================================================")
    logging.info(f"=== INICIANDO VARREDURA NACIONAL PNCP (BRASIL INTEIRO) ===")
    logging.info(f"Período de publicação: {data_inicial} até {data_final} ({dias_historico} dias)")
    logging.info(f"Total de UFs a processar: {len(ufs_alvo)}")
    logging.info(f"=======================================================\n")

    session = criar_sessao_http()
    todos_editais = []

    for uf in ufs_alvo:
        try:
            editais_uf = capturar_pncp_uf(
                uf=uf,
                data_inicial=data_inicial,
                data_final=data_final,
                session=session,
                max_paginas=max_paginas
            )
            todos_editais.extend(editais_uf)
        except Exception as e_uf:
            logging.error(f"Erro ao processar UF {uf} no PNCP: {e_uf}")

    logging.info(f"\n=== VARREDURA PNCP FINALIZADA ===")
    logging.info(f"Total Geral de Editais Futuros Encontrados: {len(todos_editais)}")

    if salvar_banco and len(todos_editais) > 0:
        backup_file = os.path.join(os.path.dirname(__file__), "editais_pncp_backup.json")
        salvar_licitacoes(todos_editais, nome_fonte="PNCP", arquivo_backup=backup_file)

    return todos_editais

def main():
    parser = argparse.ArgumentParser(description="Motor de Captação Nacional PNCP")
    parser.add_argument("--now", action="store_true", help="Executa a varredura imediatamente no terminal")
    parser.add_argument("--uf", type=str, default=None, help="Lista de UFs separadas por vírgula (ex: MA,PA,TO,SP)")
    parser.add_argument("--dias", type=int, default=3, help="Dias de histórico de publicação (padrão: 3)")
    parser.add_argument("--max-paginas", type=int, default=10, help="Máximo de páginas por modalidade (padrão: 10)")
    args = parser.parse_args()

    ufs_selecionadas = [u.strip().upper() for u in args.uf.split(",")] if args.uf else None

    if args.now:
        executar_coleta_pncp_nacional(
            ufs=ufs_selecionadas,
            dias_historico=args.dias,
            max_paginas=args.max_paginas,
            salvar_banco=True
        )
    else:
        logging.info("Agendador Nacional PNCP iniciado. Rotinas diárias às 12:00 e 18:00 (Brasília).")
        schedule.every().day.at("12:00").do(
            executar_coleta_pncp_nacional,
            ufs=ufs_selecionadas,
            dias_historico=args.dias,
            max_paginas=args.max_paginas
        )
        schedule.every().day.at("18:00").do(
            executar_coleta_pncp_nacional,
            ufs=ufs_selecionadas,
            dias_historico=args.dias,
            max_paginas=args.max_paginas
        )
        while True:
            schedule.run_pending()
            time.sleep(30)

if __name__ == "__main__":
    main()
