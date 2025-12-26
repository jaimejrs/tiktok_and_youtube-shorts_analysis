# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# --- Importações dos Módulos ---
from config import *
from styles import estetica_avancada
from database import carregar_dados_mysql, carregar_google_trends
from utils import (
    formatar_numero_br, formatar_porcentagem_br, extrair_palavras_chave, 
    gerar_gradiente_hex, atualizar_layout_grafico, plotar_grafico_linha, 
    plotar_grafico_barra, calcular_importancia_fatores, extrair_termos_engajamento, 
    testar_ab_emoji, plotar_distribuicao_ab, calcular_estatisticas_ab
)

# --- Configuração Inicial ---
st.set_page_config(layout="wide", page_title="Tiktok and Youtube Shorts Analytics", page_icon="📲", initial_sidebar_state="expanded")
estetica_avancada() 

# --- Carga de Dados ---
df_original = carregar_dados_mysql()
df_trends = carregar_google_trends()


# --- BARRA LATERAL  ---
with st.sidebar:
    st.markdown("## Filtros")
    st.markdown("---")
    if st.button("🔄 Limpar Filtros", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚙️Filtragem Principal", expanded=True):
        paises_disp = sorted(df_original['country'].unique())
        sel_paises = st.multiselect("Países", options=paises_disp, placeholder="Todos os países") or paises_disp
        plats_disp = sorted(df_original['platform'].unique())
        sel_plats = st.multiselect("Plataformas", options=plats_disp, placeholder="Todas as plataformas") or plats_disp
    with st.expander("📳Filtrar Device", expanded=False):
        dev_disp = sorted(df_original['device_type'].unique())
        sel_devs = st.multiselect("Dispositivos", options=dev_disp, placeholder="Todos os dispositivos") or dev_disp
    st.markdown("---")
    st.caption("v3.2 • Viral Analytics")

# Aplicação dos Filtros
df_filtrado = df_original.query("country in @sel_paises and platform in @sel_plats and device_type in @sel_devs")
if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros atuais.")
    st.stop()

# --- Interface Principal ---
st.title("📲 Tiktok and Youtube Shorts Analytics")
st.markdown("##### Quais fatores influenciam o sucesso viral nas plataformas de vídeos curtos ?")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Análise Geral", 
    "⚙️ Análise de Fatores", 
    "📝 Análise de Conteúdo", 
    "🌍 Análise Geográfica", 
    "🔝 Top Virais", 
    "📈 Tendências Google"
])

# ABA 1: VISÃO GERAL
with tab1:
    st.markdown("### Indicadores Gerais")
    
    # KPIs Gerais
    vis_totais = df_filtrado['views'].sum()
    eng_medio = df_filtrado['engagement_rate'].mean()
    likes_totais = df_filtrado['likes'].sum()
    total_videos = len(df_filtrado)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Visualizações Totais", formatar_numero_br(vis_totais))
    c2.metric("Engajamento Médio", formatar_porcentagem_br(eng_medio))
    c3.metric("Total Likes", formatar_numero_br(likes_totais))
    c4.metric("Vídeos Analisados", formatar_numero_br(total_videos))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Volume e Performance")
        
        # 1. Quantidade de Postagem por Mês
        df_qtd_videos = df_filtrado.groupby('year_month')['row_id'].count().reset_index()
        df_qtd_videos.columns = ['year_month', 'qtd_videos']
        df_qtd_videos['year_month'] = df_qtd_videos['year_month'].astype(str)
        
        plotar_grafico_barra(
            df=df_qtd_videos, 
            x_col='year_month', 
            y_col='qtd_videos', 
            titulo='Volume de Publicações por Mês', 
            cor=PRIMARY_COLOR,
            labels=LABELS_PT,
            formato_eixo='d'
        )

        st.divider()

        # 2. Somatório de Visualizações por Plataforma
        df_views_plat = df_filtrado.groupby('platform')['views'].sum().reset_index()

        fig_pie = px.pie(
            df_views_plat, 
            values='views', 
            names='platform', 
            hole=0.6,
            title="Soma de Visualizações por Plataforma",
            color_discrete_sequence=GERAL_PALETTE,
            labels=LABELS_PT
        )

        fig_pie.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>Total: %{value:,.0f}<br>Percentual: %{percent}"
        )

        st.plotly_chart(atualizar_layout_grafico(fig_pie), width='stretch')
        
    with col2:
        st.markdown("#### Engajamento por Mês")

        # 3. Tendência de Engajamento
        plotar_grafico_linha(
            df=df_filtrado,
            x_col='year_month', 
            y_col='engagement_rate', 
            agg_func='mean',
            titulo='Taxa de Engajamento por Mês',
            cor=SECONDARY_COLOR,
            zoom_inteligente=True,
            formato_eixo='.2%'
        )
        
        st.divider()
        
        
        st.markdown("#### Importância dos Fatores para o Engajamento")
        try:
            with st.spinner("Treinando modelo..."):
                df_imp = calcular_importancia_fatores(df_filtrado)
                plotar_grafico_barra(
                    df_imp, 
                    'Fator', 
                    'Importancia', 
                    'O que mais gera Engajamento?', 
                    cor=PRIMARY_COLOR,
                    formato_eixo='.1%'
                )
        except Exception as e:
            st.error(f"Erro ao processar modelo: {e}")

# ABA 2: FATORES
with tab2:
    st.markdown("### Fatores que Influenciam o Engajamento")
    col1, col2 = st.columns(2)
    
    with col1:
        plotar_grafico_linha(
            df_filtrado, 
            'upload_hour', 
            'engagement_rate', 
            'mean', 
            'Melhor Horário de Postagem', 
            cor='#9A10BC', 
            formato_eixo='.2%', 
            labels=LABELS_PT,
            zoom_inteligente=True
        )
        
        df_cat = df_filtrado.groupby('category')['engagement_total'].mean().reset_index().sort_values(by='engagement_total', ascending=False)
        cores = gerar_gradiente_hex(PRIMARY_COLOR, len(df_cat), valores=df_cat['engagement_total'])
        
        fig_cat = px.bar(
            df_cat, 
            x='category', 
            y='engagement_total', 
            title="Nichos de Melhor Performance (Mediana)", 
            text_auto=True, 
            color=df_cat['category'], 
            color_discrete_sequence=cores,
            labels=LABELS_PT
        )
        

        if not df_cat.empty:
            min_val = df_cat['engagement_total'].min() * 0.95 
            max_val = df_cat['engagement_total'].max() * 1.05 
            fig_cat.update_yaxes(range=[min_val, max_val]) 
            
        st.plotly_chart(atualizar_layout_grafico(fig_cat), use_container_width=True)
        
    with col2:
        bins = [0, 15, 30, 60, 120, np.inf]
        labels = ['0-15s', '15-30s', '30-60s', '60-120s', '>120s']
        df_filtrado['duration_bin'] = pd.cut(df_filtrado['duration_sec'], bins=bins, labels=labels)
        df_dur = df_filtrado.groupby('duration_bin', observed=True)['engagement_rate'].mean().reset_index()
        
        cores_dur = gerar_gradiente_hex(SECONDARY_COLOR, len(df_dur), valores=df_dur['engagement_rate'])
        
        plotar_grafico_barra(df_dur, 'duration_bin', 'engagement_rate', 'Duração Ideal', cor=cores_dur, formato_eixo='.2%', labels=LABELS_PT)
        
        # Preparação dos dados de Dia da Semana
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_day = df_filtrado.groupby('publish_dayofweek')['engagement_rate'].mean().reindex(dias_ordem).reset_index()
        
        cores_day = gerar_gradiente_hex('#fb5607', len(df_day), valores=df_day['engagement_rate'])
        

        range_dinamico = None
        if not df_day['engagement_rate'].isnull().all():
            min_day = df_day['engagement_rate'].min() * 0.98 
            max_day = df_day['engagement_rate'].max() * 1.02
            range_dinamico = [min_day, max_day]

        plotar_grafico_barra(
            df_day, 
            'publish_dayofweek', 
            'engagement_rate', 
            'Melhor Dia da Semana', 
            cor=cores_day, 
            escala_y=range_dinamico, 
            formato_eixo='.2%', 
            labels=LABELS_PT
        )

# ABA 3: CONTEÚDO
with tab3:
    st.markdown("### Análise de Conteúdo e Testes A/B")
    
    # --- BLOCO 1: ANÁLISE DOS TERMOS/TEXTO ---
    st.markdown("#### Análise de Termos presentes nos Títulos")
    col_termos1, col_termos2 = st.columns(2)
    
    with col_termos1:
        st.markdown("##### 🔠 Frequência de Termos")
        if not df_filtrado.empty:
            top_words = extrair_palavras_chave(df_filtrado['title'].dropna().tolist(), top_n=10)
            df_words = pd.DataFrame(top_words, columns=['Palavra', 'Frequência']).sort_values(by='Frequência', ascending=True)
            plotar_grafico_barra(df_words, 'Frequência', 'Palavra', 'Top 10 Termos Frequentes', cor='#3a86ff', orientation='h')
            
    with col_termos2:
        st.markdown("##### 🚀 Performance por Termo")
        if not df_filtrado.empty:
            df_termos_eng = extrair_termos_engajamento(df_filtrado['title'], df_filtrado['engagement_rate'], top_n=10)
            if not df_termos_eng.empty:
                plotar_grafico_barra(df_termos_eng.sort_values('Engajamento_Medio', ascending=True), 'Engajamento_Medio', 'Termo', 'Engajamento Médio por Termo', cor='#ff006e', orientation='h', formato_eixo='.2%')

    st.divider()

    # --- BLOCO 2: TESTE A/B DE EMOJIS ---
    st.markdown("#### O Impacto dos Emojis nos Títulos")
    col_ab_metrica, col_ab_grafico = st.columns([1, 2.5])

    with col_ab_metrica:
        df_ab = testar_ab_emoji(df_filtrado)
        eng_com = df_ab[df_ab['has_emoji'] == 1]['engagement_rate'].values[0] if not df_ab[df_ab['has_emoji'] == 1].empty else 0
        eng_sem = df_ab[df_ab['has_emoji'] == 0]['engagement_rate'].values[0] if not df_ab[df_ab['has_emoji'] == 0].empty else 0
        diff = (eng_com - eng_sem) / eng_sem if eng_sem > 0 else 0
        st.metric(label="Média com Emoji", value=formatar_porcentagem_br(eng_com), delta=f"{diff:.1%} vs Texto")
        
        t_stat, p_valor = calcular_estatisticas_ab(df_filtrado, 'has_emoji', 'engagement_rate')
        if p_valor is not None:
            st.markdown("---")
            is_significant = p_valor < 0.05
            st.markdown(f"**Confiança:** {'✅ Significativa' if is_significant else '⚠️ Inconclusiva'}")
            with st.expander("Detalhes Estatísticos"):
                st.caption(f"P-valor: {p_valor:.4f}")
                st.caption(f"Estatística T: {t_stat:.2f}")

    with col_ab_grafico:
        plotar_distribuicao_ab(df_filtrado, 'has_emoji', 'engagement_rate', "Distribuição: Com Emoji vs. Sem Emoji", {1: 'Com Emoji 🙂', 0: 'Sem Emoji ❌'})

    st.divider()

    # --- BLOCO 3: TESTE A/B: ANALISE DE ÁUDIO ---
    st.markdown(f"#### 🎵 Music Lab: Impacto de Hits Globais")
    
    # Filtro de segurança para vídeos com áudio identificado
    df_audio = df_filtrado[df_filtrado['music_track'].str.len() > 3].copy()
    
    if not df_audio.empty:
        col_mus_metrica, col_mus_grafico = st.columns([1, 2.5])
        
        with col_mus_metrica:
            total_hits = df_audio['is_global_hit'].sum()
            avg_hit = df_audio[df_audio['is_global_hit'] == 1]['engagement_rate'].mean()
            avg_normal = df_audio[df_audio['is_global_hit'] == 0]['engagement_rate'].mean()
            
            # KPIs de Performance
            st.metric("Hits Globais Identificados", f"{total_hits}")
            if total_hits > 0 and not pd.isna(avg_normal):
                diff_mus = (avg_hit - avg_normal) / avg_normal if avg_normal > 0 else 0
                st.metric("Performance de Hits", formatar_porcentagem_br(avg_hit), delta=f"{diff_mus:.1%} vs Outros")
            
            # Cálculo de Significância
            t_mus, p_mus = calcular_estatisticas_ab(df_audio, 'is_global_hit', 'engagement_rate')
            if p_mus is not None:
                st.markdown("---")
                is_significant_mus = p_mus < 0.05
                st.markdown(f"**Confiança:** {'✅ Significativa' if is_significant_mus else '⚠️ Inconclusiva'}")
                with st.expander("Ver Detalhes Estatísticos"):
                    st.caption(f"P-valor: {p_mus:.4f}")
                    st.caption(f"Estatística T: {t_mus:.2f}")

            with st.expander("Lista de Hits"):
                hits_completos = df_audio[df_audio['is_global_hit'] == 1].sort_values('views', ascending=False).drop_duplicates('music_track')
                if not hits_completos.empty:
                    for _, row in hits_completos.iterrows():
                        st.caption(f"🎶 {row['music_track']} ({formatar_numero_br(row['views'])} views)")
                else:
                    st.write("Nenhum hit global na seleção atual.")

        with col_mus_grafico:
            plotar_distribuicao_ab(
                df_audio, 'is_global_hit', 'engagement_rate', 
                "Curva de Performance: Hit Global vs. Áudio Padrão",
                {1: 'Hit Global 🌍', 0: 'Áudio Comum 💿'}
            )
    else:
        st.warning("Dados de áudio insuficientes para esta filtragem.")
        
# ABA 4: GEOGRÁFICO
with tab4:
    st.markdown("### Análises Geográficas de Performance e Engajamento")
    st.subheader("Mapa de Calor Global (Visualizações)")
    df_map = df_filtrado.groupby('country')['views'].sum().reset_index()
    df_map['iso_alpha'] = df_map['country'].str.upper().map(ISO2_TO_ISO3)
    fig_map = px.choropleth(df_map, locations="iso_alpha", color="views", hover_name="country", color_continuous_scale="Purples", labels=LABELS_PT)
    fig_map.update_geos(bgcolor='rgba(0,0,0,0)', showocean=True, oceancolor="rgba(20, 20, 40, 0.5)", showlakes=True, lakecolor="rgba(20, 20, 40, 0.5)", showcountries=True, countrycolor="#444")
    st.plotly_chart(atualizar_layout_grafico(fig_map), use_container_width=True)
    st.divider()
    st.subheader("Performance Relativa")
    df_geo = df_filtrado.groupby('country').agg(avg_views=('views', 'mean'), avg_eng=('engagement_rate', 'mean'), count=('row_id', 'count')).reset_index()
    fig_scatter = px.scatter(df_geo, x='avg_views', y='avg_eng', size='count', color='country', log_x=True, size_max=60, hover_name='country', text='country', labels=LABELS_PT, title="Views vs Engajamento")
    fig_scatter.update_traces(textposition='middle center', textfont=dict(color='white', weight='bold'))
    st.plotly_chart(atualizar_layout_grafico(fig_scatter), use_container_width=True)
    st.divider()
    st.subheader("Intensidade: Região vs Categoria")
    pivot_table = df_filtrado.pivot_table(values='engagement_rate', index='region', columns='category', aggfunc='mean')
    if not pivot_table.empty:
        fig_heat = px.imshow(pivot_table, text_auto=".2%", aspect="auto", color_continuous_scale='Purples', labels=dict(x="Categoria", y="Região", color="Engajamento"), title="Matriz de Engajamento")
        st.plotly_chart(atualizar_layout_grafico(fig_heat), use_container_width=True)
    else: st.warning("Dados insuficientes para o mapa de calor.")

# ABA 5: TOP VIRAIS
with tab5:
    st.markdown("### Ranking de Views")
    top_videos = df_filtrado.sort_values(by='views', ascending=False)
    if len(top_videos) >= 3:
        cols = st.columns(3)
        colors = [('#FFD700', '🥇 1º Lugar'), ('#C0C0C0', '🥈 2º Lugar'), ('#CD7F32', '🥉 3º Lugar')]
        for i, (col, (color, title)) in enumerate(zip(cols, colors)):
            v = top_videos.iloc[i]
            col.markdown(f"""<div style="background: rgba{tuple(int(color[1:][i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}; border: 2px solid {color}; padding: 20px; border-radius: 15px; text-align: center;"><h1 style="color: {color} !important; margin: 0;">{title}</h1><h3 style="margin: 10px 0;">{v['title']}</h3><p style="font-size: 1.5rem; color: white;">{formatar_numero_br(v['views'])} Views</p><p style="color: #bdb2ff;">{v['platform']} • {v['country']}</p></div>""", unsafe_allow_html=True)
    st.divider()
    st.subheader("📋 Lista Completa")
    st.dataframe(top_videos[['title', 'platform', 'country', 'views', 'likes', 'engagement_rate', 'category']], use_container_width=True, column_config={"title": "Título", "views": st.column_config.NumberColumn("Visualizações", format="%d"), "likes": st.column_config.NumberColumn("Likes", format="%d"), "engagement_rate": st.column_config.ProgressColumn("Engajamento", format="%.2f%%", min_value=0, max_value=float(top_videos['engagement_rate'].max())), "category": st.column_config.TextColumn("Categoria", width="medium")}, hide_index=True)

# ABA 6: GOOGLE TRENDS (REFATORADA + FILTRO)
with tab6:
    st.markdown("### Validação Externa (Google Trends)")
    
    filtro_ativo = len(df_filtrado) < len(df_original)
    
    if not df_trends.empty:
        
        # 1. Palavras que existem no banco do Google Trends
        palavras_no_trends = set(df_trends['keyword'].unique())
        
        # 2. Palavras que existem nos vídeos FILTRADOS
        palavras_do_filtro_raw = extrair_palavras_chave(df_filtrado['title'].dropna().tolist(), top_n=50)
        palavras_do_filtro = {item[0] for item in palavras_do_filtro_raw}
        
        # 3. Interseção: Só mostramos palavras que existem nos DOIS mundos
        palavras_comuns = list(palavras_no_trends.intersection(palavras_do_filtro))
        
        if not palavras_comuns:
            if filtro_ativo:
                st.warning("⚠️ As palavras-chave dos vídeos filtrados não foram encontradas no histórico do Google Trends. Mostrando todas as disponíveis.")
            opcoes_para_grafico = list(palavras_no_trends)
        else:
            if filtro_ativo:
                st.success(f"🔗 Filtrando Trends baseado nos vídeos exibidos ({len(palavras_comuns)} palavras coincidentes).")
            opcoes_para_grafico = palavras_comuns
            
        # 4. Multiselect Inteligente
        palavras_selecionadas = st.multiselect(
            "🔎 Palavras-chave:",
            options=sorted(opcoes_para_grafico),
            default=sorted(opcoes_para_grafico), # Já vem marcado o que é relevante
            placeholder="Selecione..."
        )
        
        # 5. Filtragem Final e Plotagem
        df_trends_view = df_trends[df_trends['keyword'].isin(palavras_selecionadas)]
        
        if not df_trends_view.empty:
            fig_trends = px.line(
                df_trends_view, 
                x='search_date', 
                y='interest_score', 
                color='keyword',
                title=f"Tendência de Interesse (Google Global)",
                labels=LABELS_PT,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            
            fig_trends.update_layout(hovermode="x unified")
            fig_trends.update_xaxes(dtick="M1", tickformat="%b %Y")
            
            st.plotly_chart(atualizar_layout_grafico(fig_trends), use_container_width=True)
            st.caption("Nota: O volume de busca refletido aqui é Global, mas as palavras sugeridas acima foram filtradas com base na relevância para o país/plataforma selecionado no menu lateral.")
        else:
            st.warning("Nenhuma palavra selecionada.")
            
    else:
        st.warning("⚠️ Nenhum dado de tendência encontrado. Execute scrapers/trends_validator.py.")
