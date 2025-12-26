# utils.py
import pandas as pd
import re
import colorsys
from collections import Counter
import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
from config import PRIMARY_COLOR, LABELS_PT, GERAL_PALETTE
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np
from scipy import stats

def formatar_numero_br(valor):
    """Formata números para o padrão brasileiro."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if texto.endswith(",00"): return texto[:-3]
    return texto

def formatar_porcentagem_br(valor):
    """Formata decimais para string de porcentagem brasileira."""
    return f"{valor:.2%}".replace(".", ",")

def extrair_palavras_chave(titulos, top_n=100):
    """Extrai as palavras mais frequentes dos títulos, ignorando stopwords."""
    texto_completo = " ".join(str(t) for t in titulos).lower()
    texto_limpo = re.sub(r'[^\w\s]', '', texto_completo)
    palavras = texto_limpo.split()
    
    stopwords = {
        'the', 'in', 'of', 'to', 'a', 'is', 'for', 'on', 'with', 'video', 
        'shorts', 'tiktok', 'youtube', 'de', 'em', 'para', 'com', 'e', 'do',
        'you','this','2025','try','cant', 'da', 'how', 'what', 'your'
    }
    
    palavras_filtras = [p for p in palavras if p not in stopwords and len(p) > 2]
    return Counter(palavras_filtras).most_common(top_n)

def extrair_termos_engajamento(titulos, engajamentos, top_n=10):
    """Associa palavras-chave ao engajamento médio gerado."""
    stopwords = {
        'the', 'in', 'of', 'to', 'a', 'is', 'for', 'on', 'with', 'video', 
        'shorts', 'tiktok', 'youtube', 'de', 'em', 'para', 'com', 'e', 'do',
        'you','this','2025', 'try','cant', 'da'
    }
    
    termos_data = [] 

    for titulo, eng in zip(titulos, engajamentos):
        if pd.isna(titulo): continue
        palavras = re.sub(r'[^\w\s]', '', str(titulo).lower()).split()
        
        for p in set(palavras):
            if p not in stopwords and len(p) > 2:
                termos_data.append({'Termo': p, 'Engajamento': eng})

    if not termos_data:
        return pd.DataFrame(columns=['Termo', 'Contagem', 'Engajamento_Medio'])

    df_termos = pd.DataFrame(termos_data)
    
    df_resumo = df_termos.groupby('Termo').agg(
        Contagem=('Termo', 'count'),
        Engajamento_Medio=('Engajamento', 'mean')
    ).reset_index()

    df_resumo['Engajamento_Medio'] = df_resumo['Engajamento_Medio'].fillna(0)

    return df_resumo[df_resumo['Contagem'] > 1].sort_values(by='Engajamento_Medio', ascending=False).head(top_n)

def plotar_distribuicao_ab(df, coluna_grupo, coluna_valor, titulo, labels_mapeamento):
    """Cria um gráfico de densidade (KDE) para comparação A/B profissional."""
    grupos = df[coluna_grupo].unique()
    hist_data = []
    group_labels = []
    
    for grupo in grupos:
        data = df[df[coluna_grupo] == grupo][coluna_valor].dropna()
        if not data.empty:
            hist_data.append(data)
            group_labels.append(labels_mapeamento.get(grupo, str(grupo)))

    if not hist_data:
        st.warning("Dados insuficientes para gerar a distribuição.")
        return

    fig = ff.create_distplot(
        hist_data, group_labels, 
        show_hist=False, show_rug=False,
        colors=['#3a86ff', '#fb5607']
    )

    fig.update_layout(
        title=titulo,
        xaxis_title="Taxa de Engajamento",
        yaxis_title="Densidade",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig = atualizar_layout_grafico(fig)
    st.plotly_chart(fig, width="stretch")

def gerar_gradiente_hex(base_hex, n, valores=None):
    base_hex = base_hex.lstrip("#")
    r, g, b = int(base_hex[0:2], 16) / 255, int(base_hex[2:4], 16) / 255, int(base_hex[4:6], 16) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    if valores is None:
        fatores = [(0.4 + 0.6 * (i / max(n - 1, 1))) for i in range(n)]
    else:
        min_v, max_v = min(valores), max(valores)
        amplitude = (max_v - min_v) if max_v > min_v else 1
        fatores = [0.4 + 0.6 * ((v - min_v) / amplitude) for v in valores]

    cores = []
    for f in fatores:
        new_l = min(1, max(0, l * f))
        r2, g2, b2 = colorsys.hls_to_rgb(h, new_l, s)
        cores.append("#%02x%02x%02x" % (int(r2 * 255), int(g2 * 255), int(b2 * 255)))
    return cores

def atualizar_layout_grafico(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#ffffff'},
        separators=".,",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, color='#bdb2ff'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#bdb2ff'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
    )
    return fig

def plotar_grafico_linha(df, x_col, y_col, agg_func, titulo, cor=PRIMARY_COLOR, zoom_inteligente=False, formato_eixo=None, **kwargs):
    df_agg = df.groupby(x_col)[y_col].agg(agg_func).reset_index()
    kwargs.setdefault("labels", LABELS_PT)
    fig = px.line(df_agg, x=x_col, y=y_col, markers=True, title=titulo, color_discrete_sequence=[cor], **kwargs)
    fig.update_traces(line=dict(width=3), marker=dict(size=8, line=dict(width=2, color='white')))
    fig = atualizar_layout_grafico(fig)
    if zoom_inteligente and not df_agg.empty:
        val_min, val_max = df_agg[y_col].min(), df_agg[y_col].max()
        amplitude = val_max - val_min
        margem = amplitude * 0.2 if amplitude > 0 else val_max * 0.1
        fig.update_yaxes(range=[max(0, val_min - margem), val_max + margem])
    if formato_eixo:
        fig.update_layout(yaxis_tickformat=formato_eixo)
    st.plotly_chart(fig, width="stretch")

def plotar_grafico_barra(df, x_col, y_col, titulo, cor=PRIMARY_COLOR, escala_y=None, formato_eixo=None, orientation='v', **kwargs):
    cor_seq = cor if isinstance(cor, list) else [cor]
    kwargs.setdefault("labels", LABELS_PT)
    fig = px.bar(df, x=x_col, y=y_col, title=titulo, color_discrete_sequence=cor_seq, text_auto=True, orientation=orientation, **kwargs)
    fig.update_traces(textfont_size=12, textposition="outside", cliponaxis=False)
    fig = atualizar_layout_grafico(fig)
    if formato_eixo: 
        if orientation == 'v': fig.update_layout(yaxis_tickformat=formato_eixo)
        else: fig.update_layout(xaxis_tickformat=formato_eixo)
    st.plotly_chart(fig, width="stretch")

def calcular_importancia_fatores(df):
    features = ['upload_hour', 'duration_sec', 'category', 'is_weekend']
    df_ml = df[features + ['engagement_rate']].dropna().copy()
    le = LabelEncoder()
    df_ml['category'] = le.fit_transform(df_ml['category'].astype(str))
    X, y = df_ml[features], df_ml['engagement_rate']
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    importancia = pd.DataFrame({
        'Fator': features,
        'Importancia': model.feature_importances_
    }).sort_values(by='Importancia', ascending=True)
    mapping = {**LABELS_PT, 'duration_sec': 'Duração (seg)', 'is_weekend': 'Fim de Semana?'}
    importancia['Fator'] = importancia['Fator'].map(lambda x: mapping.get(x, x))
    return importancia

def testar_ab_emoji(df):
    ab_data = df.groupby('has_emoji')['engagement_rate'].mean().reset_index()
    ab_data['Grupo'] = ab_data['has_emoji'].map({1: 'Com Emoji 🚀', 0: 'Sem Emoji 📄'})
    return ab_data

def calcular_estatisticas_ab(df, coluna_grupo, coluna_valor):
    """Calcula o Teste T e P-valor para validar a significância do teste A/B."""
    grupo_a = df[df[coluna_grupo] == 1][coluna_valor].dropna()
    grupo_b = df[df[coluna_grupo] == 0][coluna_valor].dropna()
    
    if len(grupo_a) < 2 or len(grupo_b) < 2:
        return None, None
    
    t_stat, p_valor = stats.ttest_ind(grupo_a, grupo_b, equal_var=False)
    return t_stat, p_valor