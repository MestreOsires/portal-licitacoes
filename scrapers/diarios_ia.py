"""
scrapers/diarios_ia.py - Orquestrador Modular de Diários Oficiais Estaduais e Municipais.
Utiliza o Registry Pattern (scrapers.states) para varredura multi-estado e IA/Regex.
Suporta agendamento às 12:00 e 18:00 (Brasília) e execução imediata via --now.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo
import schedule
from scrapers.core.base_scraper import FUSO_BSB
from scrapers.core.database import salvar_licitacoes
from scrapers.states import (
    STATE_REGISTRY,
    list_registered_states,
    executar_coleta_estado,
    executar_coleta_nacional_diarios
)

def executar_varredura_diarios(
    ufs: Optional[List[str]] = None,
    data_manual: Optional[str] = None
) -> int:
    """
    Executa a coleta de diários oficiais para a lista de UFs fornecida (ou todas as cadastradas).
    """
    agora = datetime.now(FUSO_BSB)
    data_alvo = agora
    if data_manual:
        try:
            data_alvo = datetime.strptime(data_manual, "%Y%m%d").replace(tzinfo=FUSO_BSB)
        except Exception:
            logging.warning(f"Data '{data_manual}' inválida. Utilizando data atual.")

    ufs_alvo = ufs if ufs else list_registered_states()
    logging.info(f"\n[Diarios] Iniciando varredura para {len(ufs_alvo)} UFs: {ufs_alvo}")

    editais = executar_coleta_nacional_diarios(ufs=ufs_alvo, data_alvo=data_alvo)

    if editais:
        backup_path = os.path.join(os.path.dirname(__file__), "editais_doema_backup.json")
        resultado = salvar_licitacoes(
            editais=editais,
            nome_fonte="DIARIOS_OFICIAIS",
            arquivo_backup=backup_path
        )
        return resultado.get("salvos", 0)

    logging.info("[Diarios] Nenhum edital futuro pendente encontrado nos diários pesquisados.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Orquestrador Nacional de Diários Oficiais")
    parser.add_argument("--now", action="store_true", help="Executa a extração imediatamente no terminal")
    parser.add_argument("--uf", type=str, default=None, help="Lista de UFs separadas por vírgula (ex: MA,PA,TO,SP)")
    parser.add_argument("--date", type=str, default=None, help="Data específica no formato YYYYMMDD (ex: 20261021)")
    parser.add_argument("--listar-estados", action="store_true", help="Lista todos os estados cadastrados no Registry")
    args = parser.parse_args()

    if args.listar_estados:
        estados = list_registered_states()
        print(f"\nEstados com Coletores Registrados no Sistema ({len(estados)}):")
        for uf in estados:
            cls = STATE_REGISTRY[uf]
            print(f"  • {uf}: {cls.NOME}")
        print()
        return

    ufs_selecionadas = [u.strip().upper() for u in args.uf.split(",")] if args.uf else None

    if args.now or args.date:
        logging.info("Execução imediata de Diários Oficiais acionada.")
        executar_varredura_diarios(ufs=ufs_selecionadas, data_manual=args.date)
    else:
        logging.info("Agendador de Diários Oficiais iniciado.")
        logging.info("Rotinas agendadas para todos os dias às 12:00 e 18:00 (Horário de Brasília).")

        schedule.every().day.at("12:00").do(
            executar_varredura_diarios,
            ufs=ufs_selecionadas,
            data_manual=args.date
        )
        schedule.every().day.at("18:00").do(
            executar_varredura_diarios,
            ufs=ufs_selecionadas,
            data_manual=args.date
        )

        while True:
            schedule.run_pending()
            time.sleep(30)

if __name__ == "__main__":
    main()
