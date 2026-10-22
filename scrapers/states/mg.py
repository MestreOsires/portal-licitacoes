"""
scrapers/states/mg.py - Coletor do Diário Oficial de Minas Gerais (Jornal Minas Gerais / IO-MG).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("MG", nome="Diário Oficial de Minas Gerais (Jornal Minas Gerais)")
class DOEMGScraper(BaseDiarioPDFScraper):
    UF = "MG"
    NOME = "DOMG"

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[MG] Iniciando coleta do Diário de Minas Gerais (Referência: {agora.strftime('%d/%m/%Y')})")

        for i in range(3):
            dt_tentativa = agora - timedelta(days=i)
            dt_str = dt_tentativa.strftime("%Y%m%d")
            url = f"https://www.jornalminasgerais.mg.gov.br/edicoes/{dt_str}/download.pdf"

            pdf_bytes = self.baixar_pdf_em_memoria(url)
            if pdf_bytes:
                logging.info(f"[MG] Edição {dt_str} obtida com sucesso ({len(pdf_bytes)/1024:.1f} KB).")
                paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                for num_pag, texto in paginas:
                    extraidos = self.extrair_editais_da_pagina(
                        texto_pagina=texto,
                        data_edicao=dt_str,
                        link_pdf=url,
                        caderno="CADERNO-1"
                    )
                    for ed in extraidos:
                        ed["fonte"] = "DOMG"
                        editais_coletados.append(ed)
                break

        logging.info(f"[MG] Total de Editais Futuros Extraídos de Minas Gerais: {len(editais_coletados)}")
        return editais_coletados
