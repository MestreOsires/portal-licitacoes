"""
scrapers/runner.py - Orquestrador Mestre do Radar de Licitações Nacional.
Centraliza a execução unificada do motor PNCP (27 UFs) e dos Diários Oficiais Estaduais/Municipais.
Agendado para rodar diariamente às 12:00 e 18:00 (Horário de Brasília).
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import schedule

# Ajusta path para importação
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.core.normalizer import TODAS_UFS, FUSO_BSB
from scrapers.pncp_api import executar_coleta_pncp_nacional
from scrapers.diarios_ia import executar_varredura_diarios
from scrapers.states import list_registered_states

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def executar_pipeline_nacional(
    ufs=None,
    fonte="all",
    dias_pncp=3,
    data_diarios=None
):
    agora = datetime.now(FUSO_BSB)
    logging.info(f"\n==================================================================")
    logging.info(f"=== INICIANDO PIPELINE DE CAPTAÇÃO NACIONAL: {agora.strftime('%d/%m/%Y %H:%M:%S')} ===")
    logging.info(f"Fonte(s): {fonte.upper()} | UFs: {ufs or 'TODAS AS 27 UFs DO BRASIL'}")
    logging.info(f"==================================================================\n")

    # 1. Captação PNCP (Brasil Inteiro ou UFs selecionadas)
    if fonte in ["all", "pncp"]:
        try:
            executar_coleta_pncp_nacional(
                ufs=ufs,
                dias_historico=dias_pncp,
                max_paginas=10,
                salvar_banco=True
            )
        except Exception as e_pncp:
            logging.error(f"[Pipeline] Erro na captação PNCP: {e_pncp}")

    # 2. Captação de Diários Oficiais Estaduais e Municipais
    if fonte in ["all", "diarios"]:
        try:
            executar_varredura_diarios(
                ufs=ufs,
                data_manual=data_diarios
            )
        except Exception as e_diarios:
            logging.error(f"[Pipeline] Erro na captação de Diários Oficiais: {e_diarios}")

    logging.info(f"\n==================================================================")
    logging.info(f"=== PIPELINE NACIONAL CONCLUÍDO COM SUCESSO! ===")
    logging.info(f"==================================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Radar de Licitações - Orquestrador Nacional")
    parser.add_argument("--now", action="store_true", help="Executa o pipeline completo imediatamente")
    parser.add_argument("--fonte", choices=["all", "pncp", "diarios"], default="all", help="Fonte a executar (padrão: all)")
    parser.add_argument("--uf", type=str, default=None, help="Lista de UFs separadas por vírgula (ex: MA,PA,TO,SP,RJ)")
    parser.add_argument("--dias", type=int, default=3, help="Dias de histórico para PNCP (padrão: 3)")
    parser.add_argument("--date", type=str, default=None, help="Data manual para diários YYYYMMDD")
    parser.add_argument("--status", action="store_true", help="Exibe status da infraestrutura e estados cobertos")
    args = parser.parse_args()

    if args.status:
        cadastrados = list_registered_states()
        print(f"\nRadar de Licitações Nacional - Status da Arquitetura:")
        print(f"  • Total de UFs no Brasil cobertas pelo PNCP: {len(TODAS_UFS)}/27")
        print(f"  • UFs com Diários Oficiais no Registry: {len(cadastrados)}/27")
        print(f"  • Horários de Execução Agendados: 12:00 e 18:00 (Brasília)\n")
        return

    ufs_selecionadas = [u.strip().upper() for u in args.uf.split(",")] if args.uf else None

    if args.now:
        logging.info("Modo imediato acionado (--now). Executando varredura...")
        executar_pipeline_nacional(
            ufs=ufs_selecionadas,
            fonte=args.fonte,
            dias_pncp=args.dias,
            data_diarios=args.date
        )
    else:
        logging.info("Iniciando Agendador Contínuo.")
        logging.info("Rotinas programadas para todos os dias às 12:00 e às 18:00 (Horário de Brasília).")

        schedule.every().day.at("12:00").do(
            executar_pipeline_nacional,
            ufs=ufs_selecionadas,
            fonte=args.fonte,
            dias_pncp=args.dias,
            data_diarios=args.date
        )
        schedule.every().day.at("18:00").do(
            executar_pipeline_nacional,
            ufs=ufs_selecionadas,
            fonte=args.fonte,
            dias_pncp=args.dias,
            data_diarios=args.date
        )

        while True:
            schedule.run_pending()
            time.sleep(30)

if __name__ == "__main__":
    main()
