"""
scrapers/states/pa.py - Coletor do Diário Oficial do Estado do Pará (IOEPA / FAMEP).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("PA", nome="Imprensa Oficial do Estado do Pará (IOEPA / FAMEP)")
class DOEPAScraper(BaseDiarioPDFScraper):
    UF = "PA"
    NOME = "IOEPA"

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[PA] Iniciando coleta do Diário do Pará (Referência: {agora.strftime('%d/%m/%Y')})")

        for i in range(4):
            dt_tentativa = agora - timedelta(days=i)
            dt_str = dt_tentativa.strftime("%Y%m%d")

            urls = [
                f"https://www.ioepa.com.br/pages/{dt_tentativa.strftime('%Y/%m/%d')}.pdf",
                f"https://diariomunicipal.com.br/famep/download/{dt_str}.pdf"
            ]

            for url in urls:
                pdf_bytes = self.baixar_pdf_em_memoria(url)
                if pdf_bytes:
                    logging.info(f"[PA] Edição {dt_str} obtida de {url} ({len(pdf_bytes)/1024:.1f} KB).")
                    paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                    for num_pag, texto in paginas:
                        extraidos = self.extrair_editais_da_pagina(
                            texto_pagina=texto,
                            data_edicao=dt_str,
                            link_pdf=url,
                            caderno="IOEPA"
                        )
                        for ed in extraidos:
                            ed["fonte"] = "IOEPA"
                            editais_coletados.append(ed)
                    if editais_coletados:
                        break

            if editais_coletados:
                break

        logging.info(f"[PA] Total de Editais Futuros Extraídos do Pará: {len(editais_coletados)}")
        return editais_coletados
