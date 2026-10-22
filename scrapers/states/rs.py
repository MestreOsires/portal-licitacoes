"""
scrapers/states/rs.py - Coletor do Diário Oficial do Rio Grande do Sul (DOE-RS / CORAG).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("RS", nome="Diário Oficial do Estado do Rio Grande do Sul (DOE-RS)")
class DOERSScraper(BaseDiarioPDFScraper):
    UF = "RS"
    NOME = "DOE-RS"

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[RS] Iniciando coleta do Diário do Rio Grande do Sul (Referência: {agora.strftime('%d/%m/%Y')})")

        for i in range(3):
            dt_tentativa = agora - timedelta(days=i)
            dt_str = dt_tentativa.strftime("%Y%m%d")
            url = f"https://www.diariooficial.rs.gov.br/materia/download/{dt_str}/diario_completo.pdf"

            pdf_bytes = self.baixar_pdf_em_memoria(url)
            if pdf_bytes:
                logging.info(f"[RS] Edição {dt_str} obtida com sucesso ({len(pdf_bytes)/1024:.1f} KB).")
                paginas = self.filtrar_paginas_relevantes(pdf_bytes)
                for num_pag, texto in paginas:
                    extraidos = self.extrair_editais_da_pagina(
                        texto_pagina=texto,
                        data_edicao=dt_str,
                        link_pdf=url,
                        caderno="ESTADUAL"
                    )
                    for ed in extraidos:
                        ed["fonte"] = "DOE-RS"
                        editais_coletados.append(ed)
                break

        logging.info(f"[RS] Total de Editais Futuros Extraídos do RS: {len(editais_coletados)}")
        return editais_coletados
