"""
scrapers/diarios_ia.py - Extração e estruturação automatizada de editais do
Diário Oficial do Estado do Maranhão (DOEMA) com IA e Fallback Heurístico em Regex.

Baixa diretamente os cadernos TE (Terceiros/Prefeituras) e EX (Executivo/Secretarias Estaduais)
da rota oficial: https://diariooficial.ma.gov.br/download.php?arqv=1&arq={caderno}{YYYYMMDD}

Aplica:
1. Retrocesso automático de data (até 3 dias) caso a edição de hoje não esteja publicada.
2. Leitura com pdfplumber em memória (BytesIO) com pré-filtro econômico de páginas.
3. Extração estruturada (OpenAI / Gemini ou Extrator Regex nativo de alta precisão).
4. Filtro estrito de Oportunidades Futuras (data_disputa >= agora).
5. Gravação direta no Supabase (tabela 'licitacoes') via upsert.
6. Agendamento diário às 12:00 e 18:00 (BRT) com suporte à flag --now para execução imediata.
"""

import os
import sys
import io
import re
import time
import json
import hashlib
import logging
import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import urllib3
import requests
import pdfplumber
import schedule
from dotenv import load_dotenv
from supabase import create_client, Client

# Desativa avisos de SSL causados pelos certificados do governo .ma.gov.br
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carrega variáveis de ambiente
load_dotenv()
load_dotenv(".env.local")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ============================================================================
# CONFIGURAÇÕES SUPABASE E IA (GEMINI / OPENAI)
# ============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info(f"Supabase conectado com sucesso ({SUPABASE_URL})")
    except Exception as e:
        logging.warning(f"Aviso ao inicializar cliente Supabase: {e}")
else:
    logging.warning("Credenciais do Supabase não encontradas no .env")

# Clientes de IA opcionais
openai_client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logging.info("OpenAI configurada com sucesso (gpt-4o-mini).")
    except Exception as e:
        logging.warning(f"Aviso ao carregar OpenAI: {e}")

gemini_model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        logging.info("Google Gemini configurado com sucesso (gemini-1.5-flash).")
    except Exception as e:
        logging.warning(f"Aviso ao carregar Gemini: {e}")

# Meses em português para decodificação de datas por extenso
MESES_PT = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12
}

# Municípios de destaque no Maranhão para resolução precisa de órgãos
MUNICIPIOS_MA = [
    "SÃO LUÍS", "SAO LUIS", "IMPERATRIZ", "SÃO JOSÉ DE RIBAMAR", "SAO JOSE DE RIBAMAR",
    "TIMON", "CAXIAS", "CODÓ", "CODO", "PAÇO DO LUMIAR", "PACO DO LUMIAR",
    "AÇAILÂNDIA", "ACAILANDIA", "BACABAL", "BALSAS", "SANTA INÊS", "SANTA INES",
    "BARRA DO CORDA", "PINHEIRO", "CHAPADINHA", "SANTA LUZIA", "BURITICUPU",
    "GRAJAÚ", "GRAJAU", "ITAPECURU MIRIM", "COROATÁ", "COROATA", "BARREIRINHAS",
    "TUTÓIA", "TUTOIA", "VIANA", "ZÉ DOCA", "ZE DOCA", "COLINAS", "CURURUPU",
    "GODOFREDO VIANA", "LAGOA DO MATO", "PRESIDENTE DUTRA", "CAROLINA", "RIACHÃO",
    "RIACHAO", "SÃO JOÃO DOS PATOS", "SAO JOAO DOS PATOS", "PEDREIRAS", "ESTREITO",
    "ARARI", "LAGO DA PEDRA", "COELHO NETO", "SANTA HELENA", "ROSÁRIO", "ROSARIO",
    "VITÓRIA DO MEARIM", "VITORIA DO MEARIM", "URBANO SANTOS", "MIRADOR", "LAGO DO JUNCO"
]

TERMOS_PRE_FILTRO = [
    "AVISO DE LICITAÇÃO", "AVISO DE LICITACAO", "PREGÃO", "PREGAO",
    "CONCORRÊNCIA", "CONCORRENCIA", "DISPENSA DE LICITAÇÃO", "DISPENSA",
    "TOMADA DE PREÇO", "TOMADA DE PRECO", "ABERTURA", "CHAMAMENTO PÚBLICO",
    "CHAMAMENTO PUBLICO", "CREDENCIAMENTO"
]

# ============================================================================
# 1. DOWNLOAD DINÂMICO DO DOEMA (TE e EX) COM RETROCESSO AUTOMÁTICO
# ============================================================================
def baixar_caderno_doema(caderno: str, data_alvo: datetime, retroceder_dias: int = 3) -> tuple:
    """
    Tenta baixar o PDF do caderno (TE ou EX) para a data informada.
    Caso não esteja disponível (não PDF ou vazio), retrocede automaticamente até N dias anteriores.
    Retorna (bytes_pdf, url_usada, data_efetiva_str).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/pdf, text/html, */*",
        "Referer": "https://diariooficial.ma.gov.br/"
    }

    for i in range(retroceder_dias + 1):
        data_tentativa = data_alvo - timedelta(days=i)
        data_str = data_tentativa.strftime("%Y%m%d")
        url = f"https://diariooficial.ma.gov.br/download.php?arqv=1&arq={caderno}{data_str}"

        try:
            logging.info(f"[{caderno}] Tentando download da edição {data_str}: {url}")
            resp = requests.get(url, headers=headers, verify=False, timeout=60)

            # Valida se o conteúdo é realmente um PDF (mágico %PDF nos primeiros 4 bytes)
            if resp.status_code == 200 and resp.content[:4] == b"%PDF" and len(resp.content) > 5000:
                logging.info(f"[{caderno}] Edição {data_str} obtida com sucesso! Tamanho: {len(resp.content) / 1024:.1f} KB")
                return resp.content, url, data_str
            else:
                logging.warning(f"[{caderno}] Edição {data_str} ainda não disponível ou sem PDF válido (len={len(resp.content)}).")
        except Exception as e:
            logging.error(f"[{caderno}] Erro ao tentar baixar edição {data_str}: {e}")

    return None, None, None

# ============================================================================
# 2. PARSER DE DATAS E HORAS (DD/MM/AAAA e Por Extenso)
# ============================================================================
def extrair_data_hora_abertura(texto: str) -> str:
    """
    Localiza a data e hora de disputa/abertura no texto do aviso.
    Ignora menções a leis como a 'Lei 14.133 de 1º de abril de 2021'.
    Retorna data em formato ISO (YYYY-MM-DDTHH:MM:SS) ou None.
    """
    # Remove ou substitui referências à Lei 14.133 de 2021 para não confundir a data
    texto_limpo = re.sub(r'Lei\s+(?:Federal\s+)?n[º°\.]?\s*14\.133[^\n]*?2021', '', texto, flags=re.IGNORECASE)

    # 1. Busca por padrões de abertura com data numérica (ex: 04/11/2026 às 09h30min)
    padrao_numerico = re.compile(
        r'(?:abertura|sess[ãa]o|disputa|realizar\s+em|recebimento)[^\n]*?(?:no dia\s+)?(\d{1,2})[\/\.](\d{1,2})[\/\.](\d{4})(?:[^\n]*?(\d{1,2})[h:](\d{2}))?',
        re.IGNORECASE
    )
    m = padrao_numerico.search(texto_limpo)
    if m:
        dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hora = int(m.group(4)) if m.group(4) else 9
        minuto = int(m.group(5)) if m.group(5) else 0
        try:
            return datetime(ano, mes, dia, hora, minuto).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass

    # 2. Busca por datas por extenso (ex: 13 de novembro de 2026, às 09h00min)
    padrao_extenso = re.compile(
        r'(?:abertura|sess[ãa]o|disputa|realizar\s+em|recebimento)[^\n]*?(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})(?:[^\n]*?(\d{1,2})[h:](\d{2}))?',
        re.IGNORECASE
    )
    m_ext = padrao_extenso.search(texto_limpo)
    if m_ext:
        dia = int(m_ext.group(1))
        mes_nome = m_ext.group(2).lower()
        ano = int(m_ext.group(3))
        mes = MESES_PT.get(mes_nome)
        if mes:
            hora = int(m_ext.group(4)) if m_ext.group(4) else 9
            minuto = int(m_ext.group(5)) if m_ext.group(5) else 0
            try:
                return datetime(ano, mes, dia, hora, minuto).strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass

    # 3. Fallback genérico para qualquer data com ano futuro (2026+) no bloco
    padrao_generico = re.compile(r'(\d{1,2})[\/\.](\d{1,2})[\/\.](202[6-9])(?:[^\n]*?(\d{1,2})[h:](\d{2}))?')
    m_gen = padrao_generico.search(texto_limpo)
    if m_gen:
        dia, mes, ano = int(m_gen.group(1)), int(m_gen.group(2)), int(m_gen.group(3))
        hora = int(m_gen.group(4)) if m_gen.group(4) else 9
        minuto = int(m_gen.group(5)) if m_gen.group(5) else 0
        try:
            return datetime(ano, mes, dia, hora, minuto).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass

    return None

# ============================================================================
# 3. EXTRATOR REGEX / HEURÍSTICO NATIVO (FALLBACK ROBUSTO SEM CUSTO DE IA)
# ============================================================================
def extrair_licitacoes_heuristicas(texto_pagina: str, data_edicao: str, link_pdf: str, caderno: str) -> list:
    """
    Extrator heurístico determinístico que identifica avisos de licitação em páginas do DOEMA.
    """
    editais = []

    # Divide a página em blocos a partir de marcadores clássicos de aviso
    delimitador = r'(?=(?:AVISO DE (?:LICITA[ÇC][ÃA]O|PREG[ÃA]O|CONCORR[ÊE]NCIA|DISPENSA|LEIL[ÃA]O|CHAMAMENTO)|Aviso de (?:Licita[çc][ãa]o|Dispensa|Preg[ãa]o)))'
    blocos = re.split(delimitador, texto_pagina, flags=re.IGNORECASE)

    # Identifica órgão geral do cabeçalho da página (se houver)
    orgao_cabecalho = "Governo do Estado do Maranhão"
    m_cab = re.search(r'(PREFEITURA MUNICIPAL DE [^\n\-–]+|SECRETARIA DE ESTADO [^\n\-–]+|EMAP|UEMA|CAEMA|DETRAN[^\n]*)', texto_pagina, re.IGNORECASE)
    if m_cab:
        orgao_cabecalho = m_cab.group(1).strip()

    for bloco in blocos:
        bloco_limpo = bloco.strip()
        if len(bloco_limpo) < 80:
            continue

        # Verifica se o bloco realmente trata de licitação
        bloco_up = bloco_limpo.upper()
        if not any(t in bloco_up for t in ["OBJETO", "PREGÃO", "PREGAO", "CONCORRÊNCIA", "DISPENSA", "ABERTURA", "SRP"]):
            continue

        # 1. Data de Abertura / Disputa
        data_disputa = extrair_data_hora_abertura(bloco_limpo)
        if not data_disputa:
            # Sem data de abertura futura confirmada -> ignora para evitar poluição
            continue

        # 2. Órgão Licitante
        orgao = orgao_cabecalho
        m_org = re.search(r'(PREFEITURA MUNICIPAL DE [^\n–-]+|PREFEITURA DE [^\n–-]+|MUNIC[IÍ]PIO DE [^\n–-]+|SECRETARIA DE ESTADO [^\n–-]+|DEPARTAMENTO [^\n–-]+|FUNDO MUNICIPAL DE [^\n–-]+)', bloco_limpo, re.IGNORECASE)
        if m_org:
            orgao = m_org.group(1).strip()

        # 3. Município do Maranhão
        municipio = "São Luís"  # Padrão capital para órgãos estaduais
        for cid in MUNICIPIOS_MA:
            if cid in orgao.upper() or cid in bloco_limpo[:300].upper():
                municipio = cid.title()
                break

        # 4. Modalidade
        modalidade = "Pregão Eletrônico"
        if "DISPENSA" in bloco_up:
            modalidade = "Dispensa Eletrônica"
        elif "CONCORRÊNCIA" in bloco_up or "CONCORRENCIA" in bloco_up:
            modalidade = "Concorrência Eletrônica"
        elif "CHAMAMENTO" in bloco_up:
            modalidade = "Chamamento Público"
        elif "LEILÃO" in bloco_up or "LEILAO" in bloco_up:
            modalidade = "Leilão"
        elif "PRESENCIAL" in bloco_up:
            modalidade = "Pregão Presencial"

        # 5. Objeto da Licitação
        objeto = "Objeto da licitação detalhado no edital do DOEMA."
        m_obj = re.search(r'OBJETO\s*:\s*([^.\n]+(?:\.[^.\n]+){0,3})', bloco_limpo, re.IGNORECASE)
        if m_obj:
            objeto = m_obj.group(1).strip()
            # Limpa quebras de linha excessivas
            objeto = re.sub(r'\s+', ' ', objeto)
        elif len(bloco_limpo) > 100:
            linhas = [l.strip() for l in bloco_limpo.split('\n') if len(l.strip()) > 20 and not l.isupper()]
            if linhas:
                objeto = " ".join(linhas[:2])

        # 6. Valor Estimado (se mencionado no aviso)
        valor_estimado = None
        m_val = re.search(r'R\$\s*([\d\.]+(?:,\d{2})?)', bloco_limpo)
        if m_val:
            try:
                val_limpo = m_val.group(1).replace(".", "").replace(",", ".")
                valor_estimado = float(val_limpo)
            except Exception:
                pass

        # 7. Número do Processo / Edital
        m_num = re.search(r'(?:N[º°o]\s*|Processo\s*[:.]?\s*)([A-Z0-9\/\.\-]+)', bloco_limpo, re.IGNORECASE)
        numero_processo = m_num.group(1).strip() if m_num else f"DOEMA-{caderno}-{data_edicao}"

        # 8. Hash único id_externo
        hash_seed = f"{caderno}-{data_edicao}-{orgao}-{objeto[:50]}-{data_disputa}"
        id_hash = hashlib.md5(hash_seed.encode("utf-8")).hexdigest()[:10]
        id_externo = f"DOEMA-{caderno}-{data_edicao}-{id_hash}"

        # 9. Esfera e Tipo de Publicação
        esfera = "Estadual" if any(k in orgao.upper() for k in ["ESTADO", "SECRETARIA", "EMAP", "UEMA", "CAEMA", "DETRAN"]) else "Municipal"
        tipo_pub = "COTACAO" if "DISPENSA" in modalidade.upper() else "AVISO"

        editais.append({
            "id_externo": id_externo,
            "orgao": orgao[:255],
            "objeto": objeto[:1000],
            "valor_estimado": valor_estimado,
            "data_disputa": data_disputa,
            "link_edital": link_pdf,
            "municipio": municipio[:100],
            "estado": "MA",
            "modalidade": modalidade[:100],
            "regiao": "Nordeste",
            "esfera": esfera,
            "tipo_publicacao": tipo_pub,
            "numero_processo": numero_processo[:50],
            "fonte": "DOEMA"
        })

    return editais

# ============================================================================
# 4. EXTRATOR COM INTELIGÊNCIA ARTIFICIAL (GEMINI / OPENAI)
# ============================================================================
def extrair_licitacoes_com_ia(texto_bloco: str, data_edicao: str, link_pdf: str, caderno: str) -> list:
    """
    Envia bloco de páginas com editais para a OpenAI ou Google Gemini estruturar em JSON.
    Se nenhuma IA estiver disponível, aciona automaticamente o extrator heurístico.
    """
    prompt = f"""
Você é um especialista em compras públicas brasileiras. Analise o seguinte extrato do Diário Oficial do Estado do Maranhão (DOEMA - Caderno {caderno}, Edição {data_edicao}).

Extraia EXCLUSIVAMENTE avisos de licitação (Pregão, Concorrência, Dispensa, Leilão, Chamamento) com abertura futura.
Ignore portarias, decretos, balanços financeiros ou atas que não sejam avisos de nova licitação.

Retorne SOMENTE um JSON Array contendo objetos com os seguintes campos:
- "orgao": Nome do órgão público ou prefeitura municipal.
- "municipio": Nome da cidade no Maranhão (se órgão estadual na capital, use "São Luís").
- "modalidade": Ex: "Pregão Eletrônico", "Concorrência Eletrônica", "Dispensa Eletrônica".
- "objeto": Descrição completa e clara do que está sendo licitado.
- "valor_estimado": float numérico ou null.
- "data_disputa": Data e hora da abertura em formato ISO 'YYYY-MM-DDTHH:MM:SS' (ex: '2026-11-04T09:30:00').
- "numero_processo": Número do edital/processo ou null.

Texto do Diário:
\"\"\"
{texto_bloco}
\"\"\"
"""

    # 1. Tentativa com OpenAI
    if openai_client:
        try:
            logging.info("Chamando OpenAI (gpt-4o-mini) para estruturação de editais...")
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um extrator de editais de diários oficiais. Responda apenas com array JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw_content = completion.choices[0].message.content
            parsed = json.loads(raw_content)
            itens = parsed if isinstance(parsed, list) else parsed.get("licitacoes") or parsed.get("editais") or list(parsed.values())[0]

            if isinstance(itens, list) and len(itens) > 0:
                formatados = []
                for it in itens:
                    hash_val = hashlib.md5(f"{it.get('orgao')}{it.get('objeto')}{it.get('data_disputa')}".encode()).hexdigest()[:8]
                    formatados.append({
                        "id_externo": f"DOEMA-{caderno}-{data_edicao}-{hash_val}",
                        "orgao": str(it.get("orgao") or "Órgão Público Estadual/Municipal - MA")[:255],
                        "objeto": str(it.get("objeto") or "Objeto publicado no DOEMA")[:1000],
                        "valor_estimado": float(it["valor_estimado"]) if it.get("valor_estimado") else None,
                        "data_disputa": it.get("data_disputa"),
                        "link_edital": link_pdf,
                        "municipio": str(it.get("municipio") or "São Luís")[:100],
                        "estado": "MA",
                        "modalidade": str(it.get("modalidade") or "Pregão Eletrônico")[:100],
                        "regiao": "Nordeste",
                        "esfera": "Estadual" if "ESTADO" in str(it.get("orgao")).upper() else "Municipal",
                        "tipo_publicacao": "COTACAO" if "dispensa" in str(it.get("modalidade")).lower() else "AVISO",
                        "numero_processo": str(it.get("numero_processo") or f"DOEMA-{data_edicao}")[:50],
                        "fonte": "DOEMA"
                    })
                return formatados
        except Exception as err_openai:
            logging.warning(f"Falha na chamada OpenAI ({err_openai}). Alternando para fallback heurístico.")

    # 2. Tentativa com Google Gemini
    if gemini_model:
        try:
            logging.info("Chamando Google Gemini (gemini-1.5-flash) para estruturação de editais...")
            response = gemini_model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            parsed = json.loads(response.text)
            itens = parsed if isinstance(parsed, list) else parsed.get("licitacoes") or parsed.get("editais") or list(parsed.values())[0]

            if isinstance(itens, list) and len(itens) > 0:
                formatados = []
                for it in itens:
                    hash_val = hashlib.md5(f"{it.get('orgao')}{it.get('objeto')}{it.get('data_disputa')}".encode()).hexdigest()[:8]
                    formatados.append({
                        "id_externo": f"DOEMA-{caderno}-{data_edicao}-{hash_val}",
                        "orgao": str(it.get("orgao") or "Órgão Público Estadual/Municipal - MA")[:255],
                        "objeto": str(it.get("objeto") or "Objeto publicado no DOEMA")[:1000],
                        "valor_estimado": float(it["valor_estimado"]) if it.get("valor_estimado") else None,
                        "data_disputa": it.get("data_disputa"),
                        "link_edital": link_pdf,
                        "municipio": str(it.get("municipio") or "São Luís")[:100],
                        "estado": "MA",
                        "modalidade": str(it.get("modalidade") or "Pregão Eletrônico")[:100],
                        "regiao": "Nordeste",
                        "esfera": "Estadual" if "ESTADO" in str(it.get("orgao")).upper() else "Municipal",
                        "tipo_publicacao": "COTACAO" if "dispensa" in str(it.get("modalidade")).lower() else "AVISO",
                        "numero_processo": str(it.get("numero_processo") or f"DOEMA-{data_edicao}")[:50],
                        "fonte": "DOEMA"
                    })
                return formatados
        except Exception as err_gemini:
            logging.warning(f"Falha na chamada Gemini ({err_gemini}). Alternando para fallback heurístico.")

    # 3. Fallback Heurístico em Regex
    return extrair_licitacoes_heuristicas(texto_bloco, data_edicao, link_pdf, caderno)

# ============================================================================
# 5. MOTOR PRINCIPAL DE PROCESSAMENTO DO DOEMA
# ============================================================================
def processar_doema(cadernos: list = None, data_manual: str = None) -> list:
    """
    Executa a captura, pré-filtragem, extração estruturada e persistência de editais futuros.
    """
    fuso_bsb = ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_bsb)

    data_base = agora
    if data_manual:
        try:
            data_base = datetime.strptime(data_manual, "%Y%m%d").replace(tzinfo=fuso_bsb)
        except Exception:
            logging.warning(f"Data manual '{data_manual}' inválida. Usando data atual.")

    cadernos_processar = cadernos or ["TE", "EX"]  # Prioriza TE (Prefeituras) e EX (Executivo)
    todos_editais_futuros = []

    logging.info(f"\n=======================================================")
    logging.info(f"=== INICIANDO CAPTURA DOEMA (Horário BSB: {agora.strftime('%d/%m/%Y %H:%M:%S')}) ===")
    logging.info(f"Cadernos: {cadernos_processar}")
    logging.info(f"=======================================================\n")

    for caderno in cadernos_processar:
        pdf_bytes, url_pdf, data_efetiva = baixar_caderno_doema(caderno, data_base, retroceder_dias=3)
        if not pdf_bytes:
            logging.warning(f"[{caderno}] Não foi possível obter nenhuma edição válida do DOEMA nos últimos 3 dias.")
            continue

        logging.info(f"[{caderno}] Analisando páginas com pdfplumber (edição {data_efetiva})...")
        paginas_relevantes = []

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                total_paginas = len(pdf.pages)
                for idx, pagina in enumerate(pdf.pages):
                    texto = pagina.extract_text() or ""
                    texto_up = texto.upper()
                    # Pré-filtro inteligente: só processa páginas com termos licitatórios
                    if any(termo in texto_up for termo in TERMOS_PRE_FILTRO):
                        paginas_relevantes.append((idx + 1, texto))

                logging.info(f"[{caderno}] Total de Páginas: {total_paginas} | Páginas Filtradas com Licitação: {len(paginas_relevantes)}")

                # Processa páginas filtradas
                for num_pag, texto_pag in paginas_relevantes:
                    # Se tiver IA configurada, envia para estruturação; caso contrário roda heurística
                    if openai_client or gemini_model:
                        extraidos = extrair_licitacoes_com_ia(texto_pag, data_efetiva, url_pdf, caderno)
                    else:
                        extraidos = extrair_licitacoes_heuristicas(texto_pag, data_efetiva, url_pdf, caderno)

                    # 4. REGRA DE OURO: FILTRO ESTRITO DE DATA FUTURA (data_disputa >= agora)
                    for edital in extraidos:
                        dt_disputa_str = edital.get("data_disputa")
                        if not dt_disputa_str:
                            continue

                        try:
                            dt_disputa_obj = datetime.fromisoformat(dt_disputa_str.replace("Z", "+00:00"))
                            if dt_disputa_obj.tzinfo is None:
                                dt_disputa_obj = dt_disputa_obj.replace(tzinfo=fuso_bsb)

                            # Só aceita se for oportunidade futura
                            if dt_disputa_obj >= agora:
                                todos_editais_futuros.append(edital)
                                logging.info(f"[{caderno} - Pág {num_pag}] Oportunidade Futura Capturada: {edital['municipio']} | {edital['modalidade']} | Disputa: {dt_disputa_str} | {edital['objeto'][:60]}...")
                            else:
                                logging.debug(f"Descartado edital expirado ({dt_disputa_str})")
                        except Exception as dt_err:
                            logging.debug(f"Erro ao comparar data: {dt_err}")

        except Exception as e_pdf:
            logging.error(f"[{caderno}] Erro ao abrir PDF com pdfplumber: {e_pdf}")

    # ============================================================================
    # 5. PERSISTÊNCIA NO SUPABASE E BACKUP LOCAL
    # ============================================================================
    logging.info(f"\n=== PROCESSAMENTO CONCLUÍDO ===")
    logging.info(f"Total de Editais Futuros Encontrados no DOEMA: {len(todos_editais_futuros)}")

    # Salva backup em JSON local para resiliência
    backup_path = os.path.join(os.path.dirname(__file__), "editais_doema_backup.json")
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(todos_editais_futuros, f, ensure_ascii=False, indent=2)
        logging.info(f"Backup local salvo em: {backup_path}")
    except Exception as e_bkp:
        logging.warning(f"Aviso ao salvar backup local: {e_bkp}")

    # Gravação no Supabase via UPSERT (on_conflict="id_externo")
    if supabase and len(todos_editais_futuros) > 0:
        sucesso = 0
        falhas = 0
        logging.info(f"Gravando {len(todos_editais_futuros)} editais futuros na tabela 'licitacoes' do Supabase...")

        for edital in todos_editais_futuros:
            try:
                supabase.table("licitacoes").upsert(edital, on_conflict="id_externo").execute()
                sucesso += 1
            except Exception as e_upsert:
                falhas += 1
                logging.error(f"Erro ao gravar edital {edital.get('id_externo')} no Supabase: {e_upsert}")

        logging.info(f"Supabase: {sucesso} editais gravados/atualizados com sucesso ({falhas} falhas).")
    elif not supabase:
        logging.warning("Supabase não disponível. Os editais foram salvos no backup local.")

    return todos_editais_futuros

# ============================================================================
# 6. ROTINA DE AGENDAMENTO (SCHEDULE 12:00 e 18:00) E CLI
# ============================================================================
def executar_rotina(data_manual: str = None, caderno_manual: str = None):
    cadernos = [caderno_manual.upper()] if caderno_manual else ["TE", "EX"]
    processar_doema(cadernos=cadernos, data_manual=data_manual)

def main():
    parser = argparse.ArgumentParser(description="Scraper e Extrator Automatizado do Diário Oficial do Maranhão (DOEMA)")
    parser.add_argument("--now", action="store_true", help="Executa a extração imediatamente no terminal")
    parser.add_argument("--date", type=str, default=None, help="Data específica no formato YYYYMMDD (ex: 20261021)")
    parser.add_argument("--caderno", type=str, default=None, help="Caderno específico para processar: TE ou EX")
    args = parser.parse_args()

    if args.now or args.date:
        logging.info("Modo de execução imediata acionado.")
        executar_rotina(data_manual=args.date, caderno_manual=args.caderno)
    else:
        logging.info("Iniciando agendador DOEMA.")
        logging.info("Rotinas programadas para todos os dias às 12:00 e às 18:00 (Horário de Brasília).")
        logging.info("Pressione Ctrl+C para encerrar.")

        schedule.every().day.at("12:00").do(executar_rotina)
        schedule.every().day.at("18:00").do(executar_rotina)

        while True:
            schedule.run_pending()
            time.sleep(30)

if __name__ == "__main__":
    main()
