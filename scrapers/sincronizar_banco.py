"""
sincronizar_banco.py - Sincroniza os editais capturados do PNCP
diretamente com a tabela 'licitacoes' no Supabase.
"""

import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("Variáveis do Supabase não encontradas no .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Colunas oficiais da tabela licitacoes no Supabase
COLUNAS_OFICIAIS = {
    "orgao", "objeto", "valor_estimado", "data_disputa", "link_edital",
    "municipio", "estado", "modalidade", "regiao", "esfera",
    "tipo_publicacao", "numero_processo", "fonte", "id_externo"
}

def limpar_registro(item: dict) -> dict:
    registro_limpo = {}
    for col in COLUNAS_OFICIAIS:
        val = item.get(col)
        # Se for estado e estiver vazio, tenta 'uf'
        if col == "estado" and not val:
            val = item.get("uf")
        registro_limpo[col] = val
    return registro_limpo

def sincronizar():
    backup_path = os.path.join(os.path.dirname(__file__), "editais_pncp_backup.json")
    if not os.path.exists(backup_path):
        logging.error(f"Arquivo '{backup_path}' não encontrado. Execute primeiro o pncp_api.py.")
        return

    with open(backup_path, "r", encoding="utf-8") as f:
        editais_raw = json.load(f)

    from datetime import datetime

    def eh_futuro(item: dict) -> bool:
        dt = item.get("data_disputa")
        if not dt:
            return False
        try:
            dt_obj = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            agora = datetime.now(dt_obj.tzinfo) if dt_obj.tzinfo else datetime.now()
            return dt_obj >= agora
        except Exception:
            return False

    editais = [limpar_registro(e) for e in editais_raw if eh_futuro(e)]

    logging.info(f"Iniciando sincronização de {len(editais)} editais futuros com o Supabase ({SUPABASE_URL})...")
    sucesso = 0
    falhas = 0

    tamanho_lote = 50
    total_lotes = (len(editais) + tamanho_lote - 1) // tamanho_lote

    for idx, i in enumerate(range(0, len(editais), tamanho_lote)):
        lote = editais[i:i + tamanho_lote]
        try:
            supabase.table("licitacoes").upsert(lote, on_conflict="id_externo").execute()
            sucesso += len(lote)
            logging.info(f"Lote {idx + 1}/{total_lotes}: {len(lote)} registros sincronizados com sucesso.")
        except Exception as err:
            logging.warning(f"Erro no lote {idx + 1}: {err}. Tentando item a item...")
            for item in lote:
                try:
                    supabase.table("licitacoes").upsert(item, on_conflict="id_externo").execute()
                    sucesso += 1
                except Exception as item_err:
                    falhas += 1
                    logging.error(f"Falha no item {item.get('id_externo')}: {item_err}")

    logging.info(f"\n==================================================")
    logging.info(f"=== SINCRONIZAÇÃO COM O SUPABASE CONCLUÍDA ===")
    logging.info(f"Total de Editais Processados: {len(editais)}")
    logging.info(f"Inseridos / Atualizados com Sucesso: {sucesso}")
    logging.info(f"Falhas: {falhas}")
    logging.info(f"==================================================\n")

if __name__ == "__main__":
    sincronizar()
