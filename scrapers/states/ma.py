"""
scrapers/states/ma.py - Coletor do Diário Oficial do Estado do Maranhão (DOEMA).
Baixa diretamente os cadernos TE (Terceiros/Prefeituras) e EX (Executivo/Secretarias).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from scrapers.core.base_scraper import register_state, FUSO_BSB
from scrapers.states.base import BaseDiarioPDFScraper

@register_state("MA", nome="Diário Oficial do Estado do Maranhão (DOEMA)")
class DOEMAScraper(BaseDiarioPDFScraper):
    UF = "MA"
    NOME = "DOEMA"

    CADERNOS = ["TE", "EX"]  # Prioriza TE (Prefeituras) e EX (Executivo)

    def coletar(self, data_alvo: Optional[datetime] = None) -> List[Dict[str, Any]]:
        agora = data_alvo or datetime.now(FUSO_BSB)
        editais_coletados = []

        logging.info(f"[MA] Iniciando coleta do DOEMA (Referência: {agora.strftime('%d/%m/%Y')})")

        for caderno in self.CADERNOS:
            pdf_bytes = None
            url_efetiva = None
            data_efetiva_str = None

            # Retrocesso automático de até 3 dias se a edição de hoje ainda não estiver publicada
            for i in range(4):
                dt_tentativa = agora - timedelta(days=i)
                dt_str = dt_tentativa.strftime("%Y%m%d")
                url = f"https://diariooficial.ma.gov.br/download.php?arqv=1&arq={caderno}{dt_str}"
                bytes_tentativa = self.baixar_pdf_em_memoria(url)
                if bytes_tentativa:
                    pdf_bytes = bytes_tentativa
                    url_efetiva = url
                    data_efetiva_str = dt_str
                    logging.info(f"[MA - {caderno}] Edição {dt_str} obtida com sucesso ({len(pdf_bytes)/1024:.1f} KB).")
                    break

            if not pdf_bytes:
                logging.warning(f"[MA - {caderno}] Não foi possível obter PDF válido nos últimos 3 dias.")
                continue

            # Filtra páginas com termos de licitação
            paginas = self.filtrar_paginas_relevantes(pdf_bytes)
            logging.info(f"[MA - {caderno}] {len(paginas)} páginas identificadas com termos de licitação.")

            for num_pag, texto in paginas:
                extraidos = self.extrair_editais_da_pagina(
                    texto_pagina=texto,
                    data_edicao=data_efetiva_str,
                    link_pdf=url_efetiva,
                    caderno=caderno
                )
                for ed in extraidos:
                    ed["fonte"] = "DOEMA"
                    editais_coletados.append(ed)

        logging.info(f"[MA] Total de Editais Futuros Extraídos do DOEMA: {len(editais_coletados)}")
        return editais_coletados
