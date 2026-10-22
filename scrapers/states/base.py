"""
scrapers/states/base.py - Classe Base com ferramentas de parsing de PDF e Regex para Diários Oficiais.
"""

import io
import re
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pdfplumber
from scrapers.core.base_scraper import BaseStateScraper, FUSO_BSB
from scrapers.core.normalizer import (
    remover_acentos,
    deduzir_regiao,
    capital_da_uf,
    deduzir_municipio,
    deduzir_esfera,
    deduzir_modalidade,
    validar_oportunidade_futura
)

MESES_PT = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12
}

TERMOS_PRE_FILTRO = [
    "AVISO DE LICITAÇÃO", "AVISO DE LICITACAO", "PREGÃO", "PREGAO",
    "CONCORRÊNCIA", "CONCORRENCIA", "DISPENSA DE LICITAÇÃO", "DISPENSA",
    "TOMADA DE PREÇO", "TOMADA DE PRECO", "ABERTURA", "CHAMAMENTO PÚBLICO",
    "CHAMAMENTO PUBLICO", "CREDENCIAMENTO", "LEILÃO", "LEILAO"
]

class BaseDiarioPDFScraper(BaseStateScraper):
    """
    Extensão para Diários Oficiais distribuídos em formato PDF.
    Oferece métodos reutilizáveis para download em memória, pré-filtragem e extração regex.
    """

    def baixar_pdf_em_memoria(self, url: str) -> Optional[bytes]:
        """Baixa o arquivo PDF diretamente em memória validando os bytes mágicos %PDF."""
        try:
            resp = requests.get(url, headers=self.headers, verify=False, timeout=self.TIMEOUT)
            if resp.status_code == 200 and resp.content[:4] == b"%PDF" and len(resp.content) > 5000:
                return resp.content
            return None
        except Exception as e:
            logging.debug(f"[{self.UF}] Falha no download de {url}: {e}")
            return None

    def filtrar_paginas_relevantes(self, pdf_bytes: bytes) -> List[Tuple[int, str]]:
        """
        Abre o PDF com pdfplumber e filtra apenas páginas com termos licitatórios.
        Economiza processamento e tokens de IA.
        """
        paginas_relevantes = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    texto = page.extract_text() or ""
                    texto_up = texto.upper()
                    if any(termo in texto_up for termo in TERMOS_PRE_FILTRO):
                        paginas_relevantes.append((idx + 1, texto))
        except Exception as e:
            logging.error(f"[{self.UF}] Erro ao inspecionar PDF: {e}")
        return paginas_relevantes

    def extrair_data_hora_abertura(self, texto: str) -> Optional[str]:
        """Localiza a data de disputa na publicação, excluindo referências a leis passadas."""
        texto_limpo = re.sub(r'Lei\s+(?:Federal\s+)?n[º°\.]?\s*14\.133[^\n]*?2021', '', texto, flags=re.IGNORECASE)

        # 1. Padrão numérico (DD/MM/AAAA às HH:MM)
        padrao_num = re.compile(
            r'(?:abertura|sess[ãa]o|disputa|realizar\s+em|recebimento)[^\n]*?(?:no dia\s+)?(\d{1,2})[\/\.](\d{1,2})[\/\.](\d{4})(?:[^\n]*?(\d{1,2})[h:](\d{2}))?',
            re.IGNORECASE
        )
        m = padrao_num.search(texto_limpo)
        if m:
            dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
            hora = int(m.group(4)) if m.group(4) else 9
            minuto = int(m.group(5)) if m.group(5) else 0
            try:
                return datetime(ano, mes, dia, hora, minuto).strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass

        # 2. Padrão por extenso (DD de mês de AAAA, às HH:MM)
        padrao_ext = re.compile(
            r'(?:abertura|sess[ãa]o|disputa|realizar\s+em|recebimento)[^\n]*?(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})(?:[^\n]*?(\d{1,2})[h:](\d{2}))?',
            re.IGNORECASE
        )
        m_ext = padrao_ext.search(texto_limpo)
        if m_ext:
            dia = int(m_ext.group(1))
            mes = MESES_PT.get(m_ext.group(2).lower())
            ano = int(m_ext.group(3))
            if mes:
                hora = int(m_ext.group(4)) if m_ext.group(4) else 9
                minuto = int(m_ext.group(5)) if m_ext.group(5) else 0
                try:
                    return datetime(ano, mes, dia, hora, minuto).strftime("%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass

        # 3. Fallback genérico para datas futuras (2026+) no bloco
        padrao_gen = re.compile(r'(\d{1,2})[\/\.](\d{1,2})[\/\.](202[6-9])(?:[^\n]*?(\d{1,2})[h:](\d{2}))?')
        m_gen = padrao_gen.search(texto_limpo)
        if m_gen:
            dia, mes, ano = int(m_gen.group(1)), int(m_gen.group(2)), int(m_gen.group(3))
            hora = int(m_gen.group(4)) if m_gen.group(4) else 9
            minuto = int(m_gen.group(5)) if m_gen.group(5) else 0
            try:
                return datetime(ano, mes, dia, hora, minuto).strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass

        return None

    def extrair_editais_da_pagina(
        self,
        texto_pagina: str,
        data_edicao: str,
        link_pdf: str,
        caderno: str = "GERAL"
    ) -> List[Dict[str, Any]]:
        """
        Extrator heurístico determinístico que identifica avisos de licitação e normaliza os dados.
        """
        editais = []
        delimitador = r'(?=(?:AVISO DE (?:LICITA[ÇC][ÃA]O|PREG[ÃA]O|CONCORR[ÊE]NCIA|DISPENSA|LEIL[ÃA]O|CHAMAMENTO)|Aviso de (?:Licita[çc][ãa]o|Dispensa|Preg[ãa]o)|PREG[ÃA]O ELETR[ÔO]NICO))'
        blocos = re.split(delimitador, texto_pagina, flags=re.IGNORECASE)

        # Identifica cabeçalho
        orgao_padrao = f"Governo do Estado de {self.UF}"
        m_cab = re.search(r'(PREFEITURA MUNICIPAL DE [^\n\-–]+|SECRETARIA DE ESTADO [^\n\-–]+|[A-ZÀ-Ú\s]{5,40}(?:PREFEITURA|MUNIC[IÍ]PIO))', texto_pagina, re.IGNORECASE)
        if m_cab:
            orgao_padrao = m_cab.group(1).strip()

        for bloco in blocos:
            bloco_limpo = bloco.strip()
            if len(bloco_limpo) < 80:
                continue

            bloco_up = bloco_limpo.upper()
            if not any(t in bloco_up for t in ["OBJETO", "PREGÃO", "PREGAO", "CONCORRÊNCIA", "DISPENSA", "ABERTURA", "SRP"]):
                continue

            # Data de disputa
            data_disputa = self.extrair_data_hora_abertura(bloco_limpo)
            if not data_disputa:
                continue

            # Filtro estrito: data_disputa >= agora
            eh_futuro, _ = validar_oportunidade_futura(data_disputa)
            if not eh_futuro:
                continue

            # Órgão
            orgao = orgao_padrao
            m_org = re.search(r'(PREFEITURA MUNICIPAL DE [^\n–-]+|PREFEITURA DE [^\n–-]+|MUNIC[IÍ]PIO DE [^\n–-]+|SECRETARIA DE ESTADO [^\n–-]+|FUNDO MUNICIPAL DE [^\n–-]+)', bloco_limpo, re.IGNORECASE)
            if m_org:
                orgao = m_org.group(1).strip()

            municipio = deduzir_municipio(orgao, self.UF)
            esfera = deduzir_esfera(orgao)
            modalidade = deduzir_modalidade(bloco_limpo)

            # Objeto
            objeto = "Objeto publicado no Diário Oficial oficial."
            m_obj = re.search(r'OBJETO\s*:\s*([^.\n]+(?:\.[^.\n]+){0,3})', bloco_limpo, re.IGNORECASE)
            if m_obj:
                objeto = re.sub(r'\s+', ' ', m_obj.group(1).strip())
            else:
                linhas = [l.strip() for l in bloco_limpo.split('\n') if len(l.strip()) > 20 and not l.isupper()]
                if linhas:
                    objeto = " ".join(linhas[:2])

            # Valor
            valor_estimado = None
            m_val = re.search(r'R\$\s*([\d\.]+(?:,\d{2})?)', bloco_limpo)
            if m_val:
                try:
                    valor_estimado = float(m_val.group(1).replace(".", "").replace(",", "."))
                except Exception:
                    pass

            # Processo
            m_num = re.search(r'(?:N[º°o]\s*|Processo\s*[:.]?\s*)([A-Z0-9\/\.\-]+)', bloco_limpo, re.IGNORECASE)
            numero_processo = m_num.group(1).strip() if m_num else f"DOE-{self.UF}-{data_edicao}"

            # Hash determinístico
            hash_seed = f"{self.UF}-{caderno}-{data_edicao}-{orgao}-{objeto[:40]}-{data_disputa}"
            id_hash = hashlib.md5(hash_seed.encode("utf-8")).hexdigest()[:10]
            id_externo = f"DOE{self.UF}-{caderno}-{data_edicao}-{id_hash}"

            tipo_pub = "COTACAO" if "dispensa" in modalidade.lower() else "AVISO"

            editais.append({
                "id_externo": id_externo,
                "orgao": orgao[:255],
                "objeto": objeto[:1000],
                "valor_estimado": valor_estimado,
                "data_disputa": data_disputa,
                "link_edital": link_pdf,
                "municipio": municipio[:100],
                "estado": self.UF,
                "modalidade": modalidade[:100],
                "regiao": deduzir_regiao(self.UF),
                "esfera": esfera,
                "tipo_publicacao": tipo_pub,
                "numero_processo": numero_processo[:50],
                "fonte": f"DOE-{self.UF}" if self.UF != "MA" else "DOEMA"
            })

        return editais
