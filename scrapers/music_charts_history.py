import json
import os
import re
import sys
import time
from difflib import SequenceMatcher
from typing import Dict, List
from urllib.parse import quote_plus

import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text

# --- CONFIGURAÇÕES ---
DB_CREDENTIALS_RAW = os.getenv('DB_CREDENTIALS')
CHART_URL = "https://kworb.net/spotify/country/global_daily.html"
MATCH_THRESHOLD = 0.72 

if not DB_CREDENTIALS_RAW:
    sys.exit(1)

creds = json.loads(DB_CREDENTIALS_RAW)

def conectar_banco():
    connection_string = f"mysql+pymysql://{creds['user']}:{quote_plus(creds['password'])}@{creds['host']}:{creds['port']}/{creds['database']}"
    return create_engine(connection_string, connect_args={"ssl": {"ssl_mode": "REQUIRED"}})

def limpar_texto(t):
    if not t: return ""
    return re.sub(r"[^\w\s]", "", str(t).lower()).strip()

def extrair_hits_do_html(html):
    soup = BeautifulSoup(html, "html.parser")
    tabela = soup.find("table", {"id": "spotifydaily"}) # ID específico do código fonte
    
    if not tabela:
        print("❌ Tabela 'spotifydaily' não encontrada.")
        return []

    hits = []
    linhas = tabela.find("tbody").find_all("tr")
    
    for linha in linhas:
        colunas = linha.find_all("td")
        if len(colunas) >= 3:
            # Pega o texto da coluna que contém 'Artista - Música'
            # No Kworb, o texto dentro da div separa os dois por " - "
            texto_completo = colunas[2].get_text(" ", strip=True)
            
            if " - " in texto_completo:
                # Divide e pega apenas a parte da Música (índice 1)
                partes = texto_completo.split(" - ", 1)
                musica = partes[1]
                
                hits.append({
                    "musica_limpa": limpar_texto(musica),
                    "rank": len(hits) + 1
                })
    
    print(f"✅ {len(hits)} hits oficiais extraídos do HTML.")
    return hits

def atualizar_dw(engine, hits_top):
    with engine.begin() as conn:
        conn.execute(text("UPDATE dim_sound SET is_global_hit = 0, chart_rank = NULL"))
        df_sons = pd.read_sql("SELECT sound_id, music_track FROM dim_sound", conn)
        
        updates = []
        for _, row in df_sons.iterrows():
            track_db = limpar_texto(row["music_track"])
            if len(track_db) < 3: continue

            for hit in hits_top:
                nome_hit = hit["musica_limpa"]
                # Lógica Híbrida: Similaridade ou Contém
                if SequenceMatcher(None, nome_hit, track_db).ratio() >= MATCH_THRESHOLD or nome_hit in track_db or track_db in nome_hit:
                    updates.append({"p_rank": hit["rank"], "p_id": row["sound_id"]})
                    break
        
        if updates:
            print(f"🚀 Enviando {len(updates)} matches para o banco...")
            batch_size = 100
            for i in range(0, len(updates), batch_size):
                conn.execute(
                    text("UPDATE dim_sound SET is_global_hit = 1, chart_rank = :p_rank WHERE sound_id = :p_id"),
                    updates[i : i + batch_size]
                )
            print("✨ Sincronização concluída!")
        else:
            print("⚠️ Nenhum vídeo no banco corresponde aos hits de hoje.")

if __name__ == "__main__":
    try:
        engine = conectar_banco()
        res = requests.get(CHART_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        ranking = extrair_hits_do_html(res.text)
        if ranking:
            atualizar_dw(engine, ranking)
    except Exception as e:
        print(f"💥 ERRO: {e}")
