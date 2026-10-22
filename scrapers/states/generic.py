"""
scrapers/states/generic.py - Coletor Genérico e Extensível para os demais Estados do Brasil.
Registra automaticamente scrapers base para UFs sem coletor customizado.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper
from scrapers.core.normalizer import TODAS_UFS

UFS_CUSTOMIZADAS = {"MA", "TO", "PA", "SP", "RJ", "MG", "BA", "PR", "RS", "GO"}
UFS_GENERICAS = [uf for uf in TODAS_UFS if uf not in UFS_CUSTOMIZADAS]

def criar_classe_generica(uf_sigla: str):
    """Cria dinamicamente uma classe de scraper para a UF genérica e a registra."""
    
    @register_state(uf_sigla, nome=f"Diário Oficial do Estado ({uf_sigla})")
    class GenericStateScraper(BaseDiarioPDFScraper):
        UF = uf_sigla
        NOME = f"DOE-{uf_sigla}"

        def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
            agora = data_alvo or datetime.now(FUSO_BSB)
            editais_coletados = []

            logging.info(f"[{self.UF}] Coletor Genérico ativado (Referência: {agora.strftime('%d/%m/%Y')})")

            # Estrutura de teste e expansão para portais estaduais padrão
            for i in range(2):
                dt_tentativa = agora - timedelta(days=i)
                dt_str = dt_tentativa.strftime("%Y%m%d")
                urls = [
                    f"https://diariooficial.{self.UF.lower()}.gov.br/edicoes/{dt_str}.pdf",
                    f"https://diariomunicipal.com.br/{self.UF.lower()}/download/{dt_str}.pdf"
                ]

                for url in urls:
                    pdf_bytes = self.baixar_pdf_em_memoria(url)
                    if pdf_bytes:
                        logging.info(f"[{self.UF}] Edição obtida de {url} ({len(pdf_bytes)/1024:.1f} KB).")
                        paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                        for num_pag, texto in paginas:
                            extraidos = self.extrair_editais_da_pagina(
                                texto_pagina=texto,
                                data_edicao=dt_str,
                                link_pdf=url,
                                caderno="GERAL"
                            )
                            for ed in extraidos:
                                ed["fonte"] = f"DOE-{self.UF}"
                                editais_coletados.append(ed)
                        if editais_coletados:
                            break

                if editais_coletados:
                    break

            logging.info(f"[{self.UF}] Coletor Genérico finalizado ({len(editais_coletados)} editais futuros).")
            return editais_coletados

    return GenericStateScraper

# Registra automaticamente todas as 17 UFs genéricas
for uf in UFS_GENERICAS:
    criar_classe_generica(uf)
