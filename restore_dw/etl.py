import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import sys
import os


# 1. CONFIGURAÇÕES


base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, CSV_NAME)
if not os.path.exists(file_path):
    parent_dir = os.path.dirname(base_dir)
    file_path = os.path.join(parent_dir, CSV_NAME)

try:
    connection_string = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    sys.exit(1)


# 2. FUNÇÕES ÚTEIS

def corrigir_data_invertida(val):
    """
    Tenta corrigir datas. Se o mês for > 8 (Setembro em diante),
    assume que houve inversão Dia/Mês (pois o dataset acaba em Agosto).
    """
    try:
        # Tenta ler no formato exótico YYYY-DD-MM primeiro
        d = pd.to_datetime(val, format='%Y-%d-%m', errors='coerce')
        
        # Se falhou, tenta padrão
        if pd.isna(d):
            d = pd.to_datetime(val, errors='coerce')
            
        if pd.isna(d): return pd.NaT

       
        if d.month > 8:
            try:
                d_corrigida = d.replace(month=d.day, day=d.month)
                return d_corrigida
            except:
                return d
        return d
    except:
        return pd.NaT

def limpar_banco(engine):
    print("\n🧹 Esvaziando tabelas (TRUNCATE)...")
    tabelas = [
        'bridge_video_hashtag', 'bridge_video_tag', 'fact_video',
        'dim_country', 'dim_platform', 'dim_language', 'dim_category',
        'dim_traffic_source', 'dim_creator', 'dim_sound', 'dim_device',
        'dim_time_bucket', 'dim_hashtag', 'dim_tag', 'dim_region'
    ]
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for t in tabelas:
            try: conn.execute(text(f"TRUNCATE TABLE {t};"))
            except: pass
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    print("Banco limpo.")

def load_dimension(df_source, col_mapping, table_name, unique_cols, lookup_col_name, engine):
    print(f" Dim: {table_name}")
    cols_csv, cols_db = list(col_mapping.keys()), list(col_mapping.values())
    unique_df = df_source[cols_csv].drop_duplicates().dropna(subset=cols_csv).copy()
    unique_df.columns = cols_db
    
    cols_str = ", ".join([f"`{c}`" for c in cols_db])
    vals = ", ".join([f":{c}" for c in cols_db])
    sql = text(f"INSERT IGNORE INTO {table_name} ({cols_str}) VALUES ({vals})")
    
    with engine.begin() as conn:
        d = unique_df.to_dict(orient='records')
        if d: conn.execute(sql, d)
            
    cols_sel = ", ".join([f"`{c}`" for c in unique_cols]) 
    id_col = f"{table_name.replace('dim_', '')}_id"
    if table_name == 'dim_category': id_col = 'category_id'
    if table_name == 'dim_traffic_source': id_col = 'traffic_source_id'
    
    lkp = pd.read_sql(f"SELECT {id_col}, {cols_sel} FROM {table_name}", engine)
    
    if len(unique_cols) > 1:
        lkp['key'] = lkp[unique_cols].apply(lambda x: tuple(x), axis=1)
        return dict(zip(lkp['key'], lkp[id_col]))
    return dict(zip(lkp[unique_cols[0]], lkp[id_col]))

# 3. PIPELINE PRINCIPAL
def main():
    print("\n Iniciando Pipeline...")
    limpar_banco(engine)
    
    try: df = pd.read_csv(file_path, encoding='utf-8')
    except: df = pd.read_csv(file_path, encoding='latin1')

    print("📅 Tratando datas ")
    df['publish_date_approx'] = df['publish_date_approx'].astype(str).str.strip().str.split(' ').str[0]
    
    df['publish_date_approx'] = df['publish_date_approx'].apply(corrigir_data_invertida)
    
    nulos = df['publish_date_approx'].isna().sum()
    if nulos > 0:
        print(f"⚠️ {nulos} linhas com datas irrecuperáveis removidas.")
        df = df.dropna(subset=['publish_date_approx'])

    data_max = df['publish_date_approx'].max()
    print(f" Nova Data Máxima: {data_max}")
    
    df['publish_date_approx'] = df['publish_date_approx'].dt.date
    df['year_month'] = pd.to_datetime(df['publish_date_approx']).dt.strftime('%Y-%m')
    df = df.replace({np.nan: None})

    # --- CARGA ---
    
    # 1. Region
    region_map = load_dimension(df, {'region': 'name'}, 'dim_region', ['name'], 'name', engine)
    df['region_id'] = df['region'].map(region_map)

    # 2. Country
    print("Dim: dim_country")
    cp = df[['country', 'region_id']].dropna().drop_duplicates()
    cp.columns = ['country_code', 'region_id']
    cp['name'] = cp['country_code']
    with engine.begin() as conn:
        for _, r in cp.iterrows():
            conn.execute(
                text("INSERT IGNORE INTO dim_country (country_code, name, region_id) VALUES (:c, :n, :r)"), 
                {'c': r['country_code'], 'n': r['name'], 'r': r['region_id']}
            )
    c_lkp = pd.read_sql("SELECT country_code, country_id FROM dim_country", engine)
    c_map = dict(zip(c_lkp['country_code'], c_lkp['country_id']))
    df['country_id'] = df['country'].map(c_map)

    p_map = load_dimension(df, {'platform': 'name'}, 'dim_platform', ['name'], 'name', engine)
    df['platform_id'] = df['platform'].map(p_map)
    l_map = load_dimension(df, {'language': 'language_code'}, 'dim_language', ['language_code'], 'language_code', engine)
    df['language_id'] = df['language'].map(l_map)
    cat_map = load_dimension(df, {'category': 'name'}, 'dim_category', ['name'], 'name', engine)
    df['category_id'] = df['category'].map(cat_map)
    t_map = load_dimension(df, {'traffic_source': 'name'}, 'dim_traffic_source', ['name'], 'name', engine)
    df['traffic_source_id'] = df['traffic_source'].map(t_map)

    # 4. Creator 
    print("Dim: dim_creator")
    cr_df = df[['author_handle', 'creator_avg_views', 'creator_tier']].dropna(subset=['author_handle']).drop_duplicates('author_handle')
    with engine.begin() as conn:
        for _, r in cr_df.iterrows():
            conn.execute(
                text("INSERT IGNORE INTO dim_creator (handle, avg_views, tier) VALUES (:h, :a, :t)"),
                {'h': r['author_handle'], 'a': r['creator_avg_views'], 't': r['creator_tier']}
            )
    cr_lkp = pd.read_sql("SELECT handle, creator_id FROM dim_creator", engine)
    cr_map = dict(zip(cr_lkp['handle'], cr_lkp['creator_id']))
    df['creator_id'] = df['author_handle'].map(cr_map)

    snd_map = load_dimension(df, {'sound_type': 'sound_type', 'music_track': 'music_track'}, 'dim_sound', ['sound_type', 'music_track'], 'x', engine)
    df['sound_id'] = df.apply(lambda x: snd_map.get((x['sound_type'], x['music_track'])), axis=1)
    
    dev_map = load_dimension(df, {'device_type': 'device_type', 'device_brand': 'device_brand'}, 'dim_device', ['device_type', 'device_brand'], 'x', engine)
    df['device_id'] = df.apply(lambda x: dev_map.get((x['device_type'], x['device_brand'])), axis=1)
    
    time_map = load_dimension(df, {'year_month': 'year_month', 'season': 'season', 'event_season': 'event_season'}, 'dim_time_bucket', ['year_month', 'season', 'event_season'], 'x', engine)
    df['time_bucket_id'] = df.apply(lambda x: time_map.get((x['year_month'], x['season'], x['event_season'])), axis=1)

    # FATO
    print(" Inserindo Fact Video...")
    col_map = {
        'row_id': 'row_id', 'platform_id': 'platform_id', 'country_id': 'country_id',
        'language_id': 'language_id', 'category_id': 'category_id', 'creator_id': 'creator_id',
        'sound_id': 'sound_id', 'device_id': 'device_id', 'traffic_source_id': 'traffic_source_id',
        'region_id': 'region_id', 'time_bucket_id': 'time_bucket_id',
        'publish_date_approx': 'publish_date_approx', 'publish_dayofweek': 'publish_dayofweek',
        'publish_period': 'publish_period', 'week_of_year': 'week_of_year',
        'upload_hour': 'upload_hour', 'is_weekend': 'is_weekend', 'title': 'title',
        'title_keywords': 'title_keywords', 'title_length': 'title_length',
        'has_emoji': 'has_emoji', 'duration_sec': 'duration_sec', 'genre': 'genre',
        'category': 'category_text', 'trend_label': 'trend_label', 'trend_type': 'trend_type',
        'trend_duration_days': 'trend_duration_days', 'engagement_velocity': 'engagement_velocity',
        'season': 'season', 'event_season': 'event_season', 'source_hint': 'source_hint',
        'notes': 'notes', 'tags': 'tags_raw', 'sample_comments': 'sample_comments',
        'device_type': 'device_type_raw', 'device_brand': 'device_brand_raw',
        'views': 'views', 'likes': 'likes', 'comments': 'comments', 'shares': 'shares',
        'saves': 'saves', 'dislikes': 'dislikes', 'creator_avg_views': 'creator_avg_views',
        'engagement_total': 'engagement_total', 'engagement_rate': 'engagement_rate',
        'like_rate': 'like_rate', 'dislike_rate': 'dislike_rate', 'comment_ratio': 'comment_ratio',
        'share_rate': 'share_rate', 'save_rate': 'save_rate', 'like_dislike_ratio': 'like_dislike_ratio',
        'engagement_per_1k': 'engagement_per_1k', 'engagement_like_rate': 'engagement_like_rate',
        'engagement_comment_rate': 'engagement_comment_rate', 'engagement_share_rate': 'engagement_share_rate',
        'avg_watch_time_sec': 'avg_watch_time_sec', 'completion_rate': 'completion_rate'
    }
    fact_df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    final_cols = list(col_map.values())
    fact_final = fact_df[[c for c in final_cols if c in fact_df.columns]].copy()
    
    try: fact_final.to_sql('fact_video', engine, if_exists='append', index=False, chunksize=2000)
    except Exception as e: print(f"⚠️ Erro Fato: {e}")

    # 7. BRIDGES
    print("🔗 Bridges...")
    v_map = dict(zip(pd.read_sql("SELECT row_id, video_id FROM fact_video", engine)['row_id'], pd.read_sql("SELECT row_id, video_id FROM fact_video", engine)['video_id']))
    df['video_id'] = df['row_id'].map(v_map)

    if 'hashtag' in df.columns:
        hts = df[['hashtag']].dropna().drop_duplicates()
        with engine.begin() as conn:
            for h in hts['hashtag']: conn.execute(text("INSERT IGNORE INTO dim_hashtag (hashtag) VALUES (:h)"), {'h': h})
        h_map = dict(zip(pd.read_sql("SELECT hashtag, hashtag_id FROM dim_hashtag", engine)['hashtag'], pd.read_sql("SELECT hashtag, hashtag_id FROM dim_hashtag", engine)['hashtag_id']))
        b = df[['video_id', 'hashtag']].dropna(); b['hashtag_id'] = b['hashtag'].map(h_map); b = b[['video_id', 'hashtag_id']].dropna().drop_duplicates()
        try: b.to_sql('bridge_video_hashtag', engine, if_exists='append', index=False)
        except: pass

    if 'tags' in df.columns:
        if 'tags_list' not in df.columns: df['tags_list'] = df['tags'].astype(str).str.split(', ')
        exp = df[['video_id', 'tags_list']].explode('tags_list').dropna(); exp['tag'] = exp['tags_list'].str.strip(); exp = exp[exp['tag']!='']
        with engine.begin() as conn:
            for t in exp['tag'].unique(): conn.execute(text("INSERT IGNORE INTO dim_tag (tag) VALUES (:t)"), {'t': t})
        t_map = dict(zip(pd.read_sql("SELECT tag, tag_id FROM dim_tag", engine)['tag'], pd.read_sql("SELECT tag, tag_id FROM dim_tag", engine)['tag_id']))
        exp['tag_id'] = exp['tag'].map(t_map); b = exp[['video_id', 'tag_id']].dropna().drop_duplicates()
        try: b.to_sql('bridge_video_tag', engine, if_exists='append', index=False)
        except: pass

    print("\n SUCESSO! Banco carregado.")

if __name__ == "__main__":
    main()
