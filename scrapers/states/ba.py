"""
scrapers/states/ba.py - Coletor do Diário Oficial do Estado da Bahia (EGBA / DOE-BA).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("BA", nome="Diário Oficial do Estado da Bahia (DOE-BA)")
class DOEBaScraper(BaseDiarioPDFScraper):
    UF = "BA"
    NOME = "DOE-BA"

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[BA] Iniciando coleta do Diário da Bahia (Referência: {agora.strftime('%d/%m/%Y')})")

        for i in range(3):
            dt_tentativa = agora - timedelta(days=i)
            dt_str = dt_tentativa.strftime("%Y%m%d")
            url = f"https://dool.egba.ba.gov.br/apifront/portal/edicoes/edicaocompleta/{dt_str}"

            pdf_bytes = self.baixar_pdf_em_memoria(url)
            if pdf_bytes:
                logging.info(f"[BA] Edição {dt_str} obtida com sucesso ({len(pdf_bytes)/1024:.1f} KB).")
                paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                for num_pag, texto in paginas:
                    extraidos = self.extrair_editais_da_pagina(
                        texto_pagina=texto,
                        data_edicao=dt_str,
                        link_pdf=url,
                        caderno="EXECUTIVO"
                    )
                    for ed in extraidos:
                        ed["fonte"] = "DOE-BA"
                        editais_coletados.append(ed)
                break

        logging.info(f"[BA] Total de Editais Futuros Extraídos da Bahia: {len(editais_coletados)}")
        return editais_coletados
