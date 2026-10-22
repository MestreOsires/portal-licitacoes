"""
scrapers/core/base_scraper.py - Classe Base e Registry Pattern para Diários Oficiais.
Permite registrar dinamicamente coletores estaduais e municipais de todo o Brasil.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, List, Optional, Any
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

FUSO_BSB = ZoneInfo("America/Sao_Paulo")

# Registro global de Scrapers por Estado (Design Pattern: Registry)
STATE_REGISTRY: Dict[str, Type["BaseStateScraper"]] = {}

def register_state(uf: str, nome: Optional[str] = None):
    """
    Decorador para registrar uma classe de scraper para uma UF específica.
    Uso:
        @register_state("MA", nome="Diário Oficial do Estado do Maranhão")
        class DOEMAScraper(BaseStateScraper):
            ...
    """
    def decorator(cls: Type["BaseStateScraper"]):
        uf_upper = uf.strip().upper()
        cls.UF = uf_upper
        cls.NOME = nome or f"Diário Oficial - {uf_upper}"
        STATE_REGISTRY[uf_upper] = cls
        return cls
    return decorator

def get_scraper_for_state(uf: str) -> Optional["BaseStateScraper"]:
    """Retorna uma instância do scraper registrado para a UF, ou None."""
    uf_upper = uf.strip().upper()
    cls = STATE_REGISTRY.get(uf_upper)
    if cls:
        return cls()
    return None

def list_registered_states() -> List[str]:
    """Retorna lista de UFs que possuem scraper implementado."""
    return sorted(list(STATE_REGISTRY.keys()))

class BaseStateScraper(ABC):
    """
    Classe Abstrata que define o contrato de coleta de qualquer Diário Oficial estadual/municipal.
    """
    UF: str = "BR"
    NOME: str = "Diário Oficial Genérico"
    TIMEOUT: int = 45

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/pdf, application/json, text/html, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
        }

    @abstractmethod
    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Executa a coleta do diário para a data_alvo (padrão hoje).
        Deve retornar uma lista de dicionários normalizados prontos para o Supabase.
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} UF={self.UF} Nome='{self.NOME}'>"
