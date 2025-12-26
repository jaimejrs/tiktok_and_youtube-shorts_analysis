import pandas as pd
from pytrends.request import TrendReq
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from collections import Counter
import sys
import os
import time
import re
import json
import warnings

# --- SILENCIAR AVISOS DE DEPRECIAÇÃO ---
warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

# --- CONFIGURAÇÕES DE SEGURANÇA ---
DB_CREDENTIALS_RAW = os.getenv('DB_CREDENTIALS')

if not DB_CREDENTIALS_RAW:
    print("❌ ERRO: Variável DB_CREDENTIALS não encontrada.")
    sys.exit(1)

try:
    creds = json.loads(DB_CREDENTIALS_RAW)
    DB_USER = creds['user']
    DB_PASS = creds['password']
    DB_HOST = creds['host']
    DB_PORT = creds['port']
    DB_NAME = creds['database']
except Exception as e:
    print(f"❌ ERRO ao processar JSON: {e}")
    sys.exit(1)

def conectar_banco():
    connection_string = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string, connect_args={"ssl": {"ssl_mode": "REQUIRED"}})

def obter_top_keywords(engine, limit=20):
    print(f"🔍 Analisando banco de dados para encontrar Top {limit} Keywords...")
    query = "SELECT title FROM fact_video WHERE title IS NOT NULL"
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    
    if df.empty:
        return []

    texto_completo = " ".join(df['title'].astype(str)).lower()
    texto_limpo = re.sub(r'[^\w\s]', '', texto_completo)
    palavras = texto_limpo.split()
    
    stopwords = {
        'the', 'in', 'of', 'to', 'a', 'is', 'for', 'on', 'with', 'video', 
        'shorts', 'tiktok', 'youtube', 'de', 'em', 'para', 'com', 'e', 'do', 
        'da', 'que', 'um', 'uma', 'and', 'my', 'pov', 'you', 'your', 'this',
        'that', 'from', 'how', 'like', 'part', 'look', 'best'
    }
    
    palavras_filtradas = [p for p in palavras if p not in stopwords and len(p) > 3]
    contagem = Counter(palavras_filtradas).most_common(limit)
    top_words = [item[0] for item in contagem]
    
    print(f"🔥 Top palavras encontradas: {top_words}")
    return top_words

def raspar_google_trends(keywords):
    if not keywords:
        return pd.DataFrame()

    print(f"🕷️ Conectando ao Google Trends para {len(keywords)} termos...")
    pytrends = TrendReq(hl='pt-BR', tz=180, timeout=(10,25))
    
    df_final = pd.DataFrame()
    tamanho_lote = 5
    lotes = [keywords[i:i + tamanho_lote] for i in range(0, len(keywords), tamanho_lote)]
    
    for i, lote in enumerate(lotes):
        print(f"   ... Processando lote {i+1}/{len(lotes)}: {lote}")
        try:
            pytrends.build_payload(lote, timeframe='today 12-m', geo='')
            time.sleep(5) 
            
            df_trends = pytrends.interest_over_time()
            
            if not df_trends.empty:
                df_trends = df_trends.reset_index()
                if 'isPartial' in df_trends.columns:
                    df_trends = df_trends.drop(columns=['isPartial'])
                
                df_melted = df_trends.melt(id_vars=['date'], var_name='keyword', value_name='interest_score')
                df_final = pd.concat([df_final, df_melted], ignore_index=True)
            else:
                print(f"   ⚠️ Lote {i+1} retornou dados vazios.")

        except Exception as e:
            print(f"   ❌ Erro no lote {i+1}: {e}")
            time.sleep(10)
    
    return df_final

def salvar_dados(engine, df):
    if df.empty:
        print("⚠️ Sem dados para salvar.")
        return

    print(f"💾 Atualizando fact_google_trends ({len(df)} registros)...")
    df.rename(columns={'date': 'search_date'}, inplace=True)
    
    with engine.begin() as conn:
        # 1. Garantir que a tabela antiga suma
        conn.execute(text("DROP TABLE IF EXISTS fact_google_trends"))
        
        # 2. Criar a tabela COM Primary Key (Exigência Aiven)
        conn.execute(text("""
            CREATE TABLE fact_google_trends (
                id INT AUTO_INCREMENT PRIMARY KEY,
                search_date DATE,
                keyword VARCHAR(255),
                interest_score INTEGER
            )
        """))
        
        # 3. Inserir dados
        df.to_sql('fact_google_trends', con=conn, if_exists='append', index=False)
        
    print("✅ Banco de dados atualizado com sucesso!")

if __name__ == "__main__":
    start_time = time.time()
    try:
        db_engine = conectar_banco()
        
        # 1. Obter termos
        termos = obter_top_keywords(db_engine, limit=20)
        
        if termos:
            # 2. Raspar
            df_resultados = raspar_google_trends(termos)
            
            # 3. Salvar
            salvar_dados(db_engine, df_resultados)
        else:
            print("⚠️ Nenhuma palavra encontrada no banco.")
            
    except Exception as exc:
        print(f"💥 ERRO CRÍTICO: {exc}")
    
    print(f"⏱️ Tempo total: {round(time.time() - start_time, 2)}s")
