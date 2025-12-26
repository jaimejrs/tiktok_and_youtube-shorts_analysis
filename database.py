# database.py
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import streamlit as st

def get_db_connection():
    if "db_credentials" in st.secrets:
        creds = st.secrets["db_credentials"]
        return (creds["DB_USER"], creds["DB_PASS"], creds["DB_HOST"], 
                creds["DB_PORT"], creds["DB_NAME"])
    else:
        st.error("Credenciais não encontradas nos Secrets (.streamlit/secrets.toml).")
        st.stop()

@st.cache_data(ttl=600)
def carregar_dados_mysql() -> pd.DataFrame:
    try:
        user, password, host, port, db = get_db_connection()
        connection_string = f"mysql+pymysql://{user}:{quote_plus(password)}@{host}:{port}/{db}"
        engine = create_engine(connection_string)
        
        query = """
        SELECT 
            v.row_id, v.title, v.publish_date_approx, v.views, v.likes, 
            v.comments, v.shares, v.engagement_rate, v.engagement_total, 
            v.duration_sec, v.upload_hour, v.publish_dayofweek, v.has_emoji,
            v.is_weekend, -- Campo adicionado para evitar KeyError no ML
            v.sample_comments,
            c.country_code AS country, p.name AS platform, cat.name AS category, 
            d.device_type, r.name AS region, t.year_month,
            s.music_track, s.is_global_hit, s.chart_rank
        FROM fact_video v
        JOIN dim_country c ON v.country_id = c.country_id
        JOIN dim_platform p ON v.platform_id = p.platform_id
        JOIN dim_category cat ON v.category_id = cat.category_id
        JOIN dim_device d ON v.device_id = d.device_id
        JOIN dim_region r ON v.region_id = r.region_id
        JOIN dim_time_bucket t ON v.time_bucket_id = t.time_bucket_id
        JOIN dim_sound s ON v.sound_id = s.sound_id
        """
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        # Tratamento de datas e períodos
        df['publish_date_approx'] = pd.to_datetime(df['publish_date_approx'])
        df['year_month'] = df['publish_date_approx'].dt.to_period('M').astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do MySQL: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_google_trends():
    try:
        user, password, host, port, db = get_db_connection()
        connection_string = f"mysql+pymysql://{user}:{quote_plus(password)}@{host}:{port}/{db}"
        engine = create_engine(connection_string)
        
        query = "SELECT * FROM fact_google_trends ORDER BY search_date"
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            
        if not df.empty:
            df['search_date'] = pd.to_datetime(df['search_date'])
        return df
    except Exception as e:
        return pd.DataFrame()
