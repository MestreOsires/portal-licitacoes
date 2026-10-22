"""
scrapers/states/__init__.py - Registry Central de Diários Oficiais Estaduais.
Importa todos os módulos de estados e disponibiliza o catálogo nacional de scrapers.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Importa a infraestrutura do Registry
from scrapers.core.base_scraper import (
    STATE_REGISTRY,
    BaseStateScraper,
    register_state,
    get_scraper_for_state,
    list_registered_states
)

# Importa os módulos customizados para disparar o registro automático
from scrapers.states import ma
from scrapers.states import to
from scrapers.states import pa
from scrapers.states import sp
from scrapers.states import rj
from scrapers.states import mg
from scrapers.states import ba
from scrapers.states import pr
from scrapers.states import rs
from scrapers.states import go
from scrapers.states import generic  # Registra dinamicamente as 17 UFs restantes

def executar_coleta_estado(uf: str, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Executa o scraper específico de uma UF com isolamento de falha."""
    scraper = get_scraper_for_state(uf)
    if not scraper:
        logging.warning(f"[Registry] Nenhum coletor cadastrado para a UF '{uf}'.")
        return []

    try:
        logging.info(f"[Registry] Executando coletor para {uf}: {scraper.NOME}")
        return scraper.coletar(data_alvo=data_alvo)
    except Exception as err:
        logging.error(f"[Registry] Erro inesperado na coleta de {uf} ({scraper.NOME}): {err}")
        return []

def executar_coleta_nacional_diarios(ufs: Optional[List[str]] = None, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Executa a varredura de Diários Oficiais para a lista de UFs (ou todo o Brasil).
    Garante resiliência: se um estado falhar, os outros continuam sem interrupção.
    """
    ufs_alvo = [u.upper().strip() for u in ufs] if ufs else list_registered_states()
    todos_editais = []

    logging.info(f"\n=======================================================")
    logging.info(f"=== INICIANDO VARREDURA NACIONAL DE DIÁRIOS OFICIAIS ===")
    logging.info(f"UFs Selecionadas ({len(ufs_alvo)}): {ufs_alvo}")
    logging.info(f"=======================================================\n")

    for uf in ufs_alvo:
        try:
            editais_uf = executar_coleta_estado(uf, data_alvo=data_alvo)
            todos_editais.extend(editais_uf)
        except Exception as e:
            logging.error(f"[Registry] Erro crítico isolado na UF {uf}: {e}")

    logging.info(f"\n=== VARREDURA NACIONAL DE DIÁRIOS CONCLUÍDA ===")
    logging.info(f"Total de Editais Futuros Coletados: {len(todos_editais)}\n")
    return todos_editais

__all__ = [
    "STATE_REGISTRY",
    "BaseStateScraper",
    "register_state",
    "get_scraper_for_state",
    "list_registered_states",
    "executar_coleta_estado",
    "executar_coleta_nacional_diarios"
]
