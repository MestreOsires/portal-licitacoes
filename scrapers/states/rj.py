"""
scrapers/states/rj.py - Coletor do Diário Oficial do Estado do Rio de Janeiro (DOERJ).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("RJ", nome="Diário Oficial do Estado do Rio de Janeiro (DOERJ)")
class DOERJScraper(BaseDiarioPDFScraper):
    UF = "RJ"
    NOME = "DOERJ"

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[RJ] Iniciando coleta do DOERJ (Referência: {agora.strftime('%d/%m/%Y')})")

        for i in range(3):
            dt_tentativa = agora - timedelta(days=i)
            dt_str = dt_tentativa.strftime("%Y%m%d")
            url = f"https://www.ioerj.com.br/portal/modules/conteudoonline/do_download.php?data={dt_str}&caderno=1"

            pdf_bytes = self.baixar_pdf_em_memoria(url)
            if pdf_bytes:
                logging.info(f"[RJ] Edição {dt_str} obtida com sucesso ({len(pdf_bytes)/1024:.1f} KB).")
                paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                for num_pag, texto in paginas:
                    extraidos = self.extrair_editais_da_pagina(
                        texto_pagina=texto,
                        data_edicao=dt_str,
                        link_pdf=url,
                        caderno="PARTE-1"
                    )
                    for ed in extraidos:
                        ed["fonte"] = "DOERJ"
                        editais_coletados.append(ed)
                break

        logging.info(f"[RJ] Total de Editais Futuros Extraídos do DOERJ: {len(editais_coletados)}")
        return editais_coletados
