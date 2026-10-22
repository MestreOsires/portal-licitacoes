"""
scrapers/core/__init__.py
"""

from scrapers.core.normalizer import (
    TODAS_UFS,
    UF_INFO,
    remover_acentos,
    normalizar_uf,
    deduzir_regiao,
    capital_da_uf,
    obter_coordenadas,
    deduzir_municipio,
    deduzir_esfera,
    deduzir_modalidade,
    validar_oportunidade_futura
)
from scrapers.core.database import (
    obter_cliente_supabase,
    salvar_licitacoes,
    sanitizar_registro
)
from scrapers.core.base_scraper import (
    BaseStateScraper,
    register_state,
    get_scraper_for_state,
    list_registered_states,
    STATE_REGISTRY
)

__all__ = [
    "TODAS_UFS",
    "UF_INFO",
    "remover_acentos",
    "normalizar_uf",
    "deduzir_regiao",
    "capital_da_uf",
    "obter_coordenadas",
    "deduzir_municipio",
    "deduzir_esfera",
    "deduzir_modalidade",
    "validar_oportunidade_futura",
    "obter_cliente_supabase",
    "salvar_licitacoes",
    "sanitizar_registro",
    "BaseStateScraper",
    "register_state",
    "get_scraper_for_state",
    "list_registered_states",
    "STATE_REGISTRY"
]
