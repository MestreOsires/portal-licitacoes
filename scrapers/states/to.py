"""
scrapers/states/to.py - Coletor do Diário Oficial do Estado do Tocantins (DOE-TO).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("TO", nome="Diário Oficial do Estado do Tocantins (DOE-TO)")
class DOETOScraper(BaseDiarioPDFScraper):
    UF = "TO"
    NOME = "DOE-TO"

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[TO] Iniciando coleta do DOE-TO (Referência: {agora.strftime('%d/%m/%Y')})")

        # Tenta a rota de diários do Tocantins com retrocesso
        for i in range(4):
            dt_tentativa = agora - timedelta(days=i)
            dt_str = dt_tentativa.strftime("%Y%m%d")
            dt_barra = dt_tentativa.strftime("%Y/%m/%d")

            urls_tentar = [
                f"https://diariooficial.to.gov.br/diario/{dt_barra}/download",
                f"https://diariomunicipal.com.br/atm/download/{dt_str}.pdf"
            ]

            for url in urls_tentar:
                pdf_bytes = self.baixar_pdf_em_memoria(url)
                if pdf_bytes:
                    logging.info(f"[TO] Edição {dt_str} obtida de {url} ({len(pdf_bytes)/1024:.1f} KB).")
                    paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                    for num_pag, texto in paginas:
                        extraidos = self.extrair_editais_da_pagina(
                            texto_pagina=texto,
                            data_edicao=dt_str,
                            link_pdf=url,
                            caderno="ESTADUAL"
                        )
                        for ed in extraidos:
                            ed["fonte"] = "DOE-TO"
                            editais_coletados.append(ed)
                    if editais_coletados:
                        break

            if editais_coletados:
                break

        logging.info(f"[TO] Total de Editais Futuros Extraídos do DOE-TO: {len(editais_coletados)}")
        return editais_coletados
