"""
scrapers/core/database.py - Conexão, persistência e governança de dados no Supabase.
Garante o cumprimento estrito do schema oficial e a política de oportunidades futuras.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from scrapers.core.normalizer import validar_oportunidade_futura

load_dotenv()
load_dotenv(".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

COLUNAS_OFICIAIS = {
    "id_externo", "orgao", "objeto", "valor_estimado", "data_disputa",
    "link_edital", "municipio", "estado", "modalidade", "regiao",
    "esfera", "tipo_publicacao", "numero_processo", "coordenadas", "fonte"
}

_client: Optional[Client] = None

def obter_cliente_supabase() -> Optional[Client]:
    """Retorna instância singleton do cliente Supabase."""
    global _client
    if _client is not None:
        return _client
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logging.info(f"[Database] Conectado ao Supabase: {SUPABASE_URL}")
        except Exception as err:
            logging.error(f"[Database] Erro ao conectar ao Supabase: {err}")
    return _client

def sanitizar_registro(item: Dict[str, Any]) -> Dict[str, Any]:
    """Limpa o registro mantendo estritamente as colunas suportadas no Supabase."""
    registro = {}
    for col in COLUNAS_OFICIAIS:
        val = item.get(col)
        # Compatibilidade com campo legado 'uf'
        if col == "estado" and not val:
            val = item.get("uf")
        registro[col] = val
    return registro

def salvar_licitacoes(
    editais: List[Dict[str, Any]],
    nome_fonte: str = "NACIONAL",
    arquivo_backup: Optional[str] = None,
    batch_size: int = 50
) -> Dict[str, int]:
    """
    Persiste uma lista de editais no Supabase aplicando o filtro estrito de data futura.
    Também grava cópia de contingência em JSON local.
    """
    total_recebidos = len(editais)
    editais_futuros = []

    # 1. Filtro estrito: data_disputa >= agora
    for e in editais:
        dt = e.get("data_disputa")
        eh_futuro, _ = validar_oportunidade_futura(dt)
        if eh_futuro:
            editais_futuros.append(sanitizar_registro(e))

    descartados = total_recebidos - len(editais_futuros)
    if descartados > 0:
        logging.info(f"[{nome_fonte}] {descartados} editais passados/sem data válida foram descartados.")

    # 2. Backup local de segurança
    if arquivo_backup and len(editais_futuros) > 0:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(arquivo_backup)), exist_ok=True)
            with open(arquivo_backup, "w", encoding="utf-8") as f:
                json.dump(editais_futuros, f, ensure_ascii=False, indent=2)
            logging.info(f"[{nome_fonte}] Backup salvo: {arquivo_backup} ({len(editais_futuros)} editais)")
        except Exception as bkp_err:
            logging.warning(f"[{nome_fonte}] Aviso ao salvar backup local: {bkp_err}")

    # 3. Persistência no Supabase via upsert em lotes
    client = obter_cliente_supabase()
    if not client:
        logging.warning(f"[{nome_fonte}] Supabase offline. Editais persistidos apenas no backup local.")
        return {"processados": total_recebidos, "futuros": len(editais_futuros), "salvos": 0, "falhas": 0}

    salvos = 0
    falhas = 0

    for i in range(0, len(editais_futuros), batch_size):
        lote = editais_futuros[i:i + batch_size]
        try:
            client.table("licitacoes").upsert(lote, on_conflict="id_externo").execute()
            salvos += len(lote)
        except Exception as batch_err:
            logging.warning(f"[{nome_fonte}] Erro no lote {i//batch_size + 1}: {batch_err}. Tentando item a item...")
            for item in lote:
                try:
                    client.table("licitacoes").upsert(item, on_conflict="id_externo").execute()
                    salvos += 1
                except Exception as item_err:
                    falhas += 1
                    logging.error(f"[{nome_fonte}] Falha no id_externo {item.get('id_externo')}: {item_err}")

    logging.info(f"[{nome_fonte}] Conclusão: {salvos} editais futuros salvos no Supabase ({falhas} falhas).")
    return {"processados": total_recebidos, "futuros": len(editais_futuros), "salvos": salvos, "falhas": falhas}
