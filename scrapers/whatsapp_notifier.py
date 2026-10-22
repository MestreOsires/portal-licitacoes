"""
whatsapp_notifier.py - Motor de Alertas Ativos via WhatsApp para Licitações.
Varre os alertas cadastrados pelos usuários, localiza editais correspondentes por
palavra-chave e geolocalização, e envia notificações automáticas no WhatsApp.
Agendado para rodar diariamente às 12:00 e 18:00 (Horário de Brasília).
"""

import os
import time
import logging
from datetime import datetime, timedelta
import pytz
import requests
import schedule
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Configurações da API de WhatsApp (Compatível com Evolution API, Z-API ou Gateway Genérico)
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://api.whatsapp-gateway.com/send-message")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")
WHATSAPP_INSTANCE_ID = os.getenv("WHATSAPP_INSTANCE_ID", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
else:
    logging.warning("Supabase não configurado no .env.")

def formatar_moeda(valor):
    if not valor:
        return "Não informado"
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)

def formatar_data(data_iso):
    if not data_iso:
        return "A definir"
    try:
        dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        fuso_bsb = pytz.timezone("America/Sao_Paulo")
        dt_local = dt.astimezone(fuso_bsb)
        return dt_local.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return data_iso[:16]

def enviar_whatsapp(numero_destinatario: str, mensagem: str) -> bool:
    """
    Envia a mensagem via gateway de WhatsApp configurado.
    """
    numero_limpo = "".join(filter(str.isdigit, numero_destinatario))
    if not numero_limpo.startswith("55") and len(numero_limpo) in [10, 11]:
        numero_limpo = "55" + numero_limpo

    logging.info(f"Disparando alerta via WhatsApp para {numero_limpo}...")

    # Se a API de WhatsApp não estiver com chave configurada, simula o envio no log
    if not WHATSAPP_API_KEY:
        logging.info(f"[SIMULAÇÃO WHATSAPP] Mensagem enviada para {numero_limpo}:\n{mensagem}\n")
        return True

    headers = {
        "Content-Type": "application/json",
        "apikey": WHATSAPP_API_KEY,
        "Authorization": f"Bearer {WHATSAPP_API_KEY}"
    }

    payload = {
        "number": numero_limpo,
        "phone": numero_limpo,
        "message": mensagem,
        "text": mensagem
    }

    try:
        resp = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=15)
        if resp.status_code in [200, 201]:
            logging.info(f"Mensagem enviada com sucesso para {numero_limpo}!")
            return True
        else:
            logging.error(f"Falha ao enviar WhatsApp: Status {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logging.error(f"Erro de conexão com API do WhatsApp: {e}")
        return False

def processar_alertas():
    """
    Busca todos os alertas ativos e dispara mensagens para os editais encontrados.
    """
    if not supabase:
        logging.error("Supabase indisponível para verificar alertas.")
        return

    logging.info("Iniciando verificação de alertas ativos...")

    try:
        # Busca alertas ativos com dados do usuário associado
        resp_alertas = supabase.table("alertas").select("*, usuarios(*)").eq("ativo", True).execute()
        alertas = resp_alertas.data or []

        if not alertas:
            logging.info("Nenhum alerta ativo encontrado no momento.")
            return

        logging.info(f"{len(alertas)} alertas ativos encontrados para processamento.")

        # Busca licitações recentes (últimas 24 horas)
        agora = datetime.now(pytz.utc)
        limite_tempo = (agora - timedelta(hours=24)).isoformat()

        resp_licitacoes = supabase.table("licitacoes") \
            .select("*") \
            .gte("created_at", limite_tempo) \
            .order("created_at", desc=True) \
            .execute()
        
        licitacoes_recentes = resp_licitacoes.data or []
        logging.info(f"{len(licitacoes_recentes)} editais recentes encontrados nas últimas 24h.")

        for alerta in alertas:
            usuario = alerta.get("usuarios")
            if not usuario:
                continue

            destinatario_tel = usuario.get("telefone_whatsapp")
            destinatario_nome = usuario.get("nome", "Assinante")
            palavras_chave = [p.lower().strip() for p in alerta.get("palavras_chave", []) if p]

            if not palavras_chave:
                continue

            for edital in licitacoes_recentes:
                objeto = (edital.get("objeto") or "").lower()
                orgao = (edital.get("orgao") or "").lower()

                # Verifica se alguma palavra-chave está no objeto ou órgão
                termo_encontrado = next((termo for termo in palavras_chave if termo in objeto or termo in orgao), None)

                if termo_encontrado:
                    # Monta mensagem atraente no formato de texto do WhatsApp
                    mensagem = (
                        f"🚨 *NOVO EDITAL DETECTADO NO RADAR!* 🚨\n"
                        f"Olá, *{destinatario_nome}*! Encontramos uma oportunidade com a palavra-chave *\"{termo_encontrado}\"*:\n\n"
                        f"🏛️ *Órgão:* {edital.get('orgao')}\n"
                        f"📍 *Local:* {edital.get('municipio')} - {edital.get('estado')}\n"
                        f"💰 *Valor Estimado:* {formatar_moeda(edital.get('valor_estimado'))}\n"
                        f"📅 *Data da Disputa:* {formatar_data(edital.get('data_disputa'))}\n"
                        f"🌐 *Fonte:* {edital.get('fonte')}\n\n"
                        f"📋 *Objeto:* \n{edital.get('objeto')[:280]}...\n\n"
                        f"📄 *Acesse o Edital Completo:* \n{edital.get('link_edital') or 'https://pncp.gov.br'}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🔔 _Você recebe este alerta com base no seu radar cadastrado._"
                    )

                    enviar_whatsapp(destinatario_tel, mensagem)
                    time.sleep(1)  # Intervalo de segurança anti-ban do WhatsApp

    except Exception as e:
        logging.error(f"Erro ao processar alertas de WhatsApp: {e}")

def agendador():
    """
    Agenda o envio de alertas para as 12:00 e 18:00 (Horário de Brasília).
    """
    logging.info("Agendador de WhatsApp ativo (Horários: 12:00 e 18:00 - Brasília).")

    schedule.every().day.at("12:00").do(processar_alertas)
    schedule.every().day.at("18:00").do(processar_alertas)

    # Executa verificação inicial de inicialização
    processar_alertas()

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    agendador()
