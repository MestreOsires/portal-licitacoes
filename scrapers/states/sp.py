"""
scrapers/states/sp.py - Coletor do Diário Oficial do Estado de São Paulo (DOE-SP / Imprensa Oficial).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("SP", nome="Diário Oficial do Estado de São Paulo (DOE-SP)")
class DOESPScraper(BaseDiarioPDFScraper):
    UF = "SP"
    NOME = "DOE-SP"

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[SP] Iniciando coleta do DOE-SP (Referência: {agora.strftime('%d/%m/%Y')})")

        for i in range(3):
            dt_tentativa = agora - timedelta(days=i)
            dt_str = dt_tentativa.strftime("%Y%m%d")
            url = f"https://www.imprensaoficial.com.br/DO/BuscaDO2001Documento_11_4.aspx?link=/executivo/{dt_str}.pdf"

            pdf_bytes = self.baixar_pdf_em_memoria(url)
            if pdf_bytes:
                logging.info(f"[SP] Edição {dt_str} obtida com sucesso ({len(pdf_bytes)/1024:.1f} KB).")
                paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                for num_pag, texto in paginas:
                    extraidos = self.extrair_editais_da_pagina(
                        texto_pagina=texto,
                        data_edicao=dt_str,
                        link_pdf=url,
                        caderno="EXECUTIVO"
                    )
                    for ed in extraidos:
                        ed["fonte"] = "DOE-SP"
                        editais_coletados.append(ed)
                break

        logging.info(f"[SP] Total de Editais Futuros Extraídos do DOE-SP: {len(editais_coletados)}")
        return editais_coletados
