# styles.py
import streamlit as st
import random

def estetica_avancada():
    CORES_ROXAS = ['#8338ec', '#9d4edd', '#e0aaff', '#c77dff', '#7b2cbf', '#ffffff']
    particulas_html = ""

    # Geração de partículas
    for i in range(100):
        left = random.randint(0, 100) 
        size = random.randint(3, 8)   
        duration = random.randint(15, 30)  
        delay = random.randint(0, 20)
        opacity = random.uniform(0.4, 0.9)  
        color = random.choice(CORES_ROXAS)
        particulas_html += f"""
        <div class="particle" style="
            left: {left}%;
            width: {size}px;
            height: {size}px;
            animation-duration: {duration}s;
            animation-delay: {delay}s;
            opacity: {opacity};
            background-color: {color};
            box-shadow: 0 0 {size*2}px {color};
        "></div>
        """

    st.markdown(f"""
        <style>
            /* --- CONFIGURAÇÃO GERAL DO APP --- */
            .stApp {{
                background: radial-gradient(circle at 50% 10%, rgb(25, 10, 50) 0%, rgb(5, 5, 10) 100%);
                color: #ffffff;
                overflow-x: hidden;
            }}

            /* --- FORÇAR TEXTOS CLAROS --- */
            [data-testid="stMetricLabel"] {{
                color: #e0aaff !important;
                font-size: 1rem !important;
                font-weight: 600 !important;
            }}
            [data-testid="stMetricValue"] {{
                color: #ffffff !important;
                text-shadow: 0 0 10px rgba(131, 56, 236, 0.5);
            }}

            /* --- ANIMAÇÃO DAS PARTÍCULAS --- */
            @keyframes floatUp {{
                0% {{ transform: translateY(110vh) translateX(0px) rotate(0deg); opacity: 0; }}
                15% {{ opacity: 1; }}
                100% {{ transform: translateY(-10vh) translateX({{random.randint(-50, 50)}}px) rotate(360deg); opacity: 0; }}
            }}

            .particle {{
                position: fixed; bottom: -10px; border-radius: 50%; pointer-events: none; z-index: 0; 
                animation: floatUp linear infinite;
            }}

            .block-container {{ z-index: 1; position: relative; }}

            [data-testid="stSidebar"] {{
                background-color: rgba(10, 5, 20, 0.9);
                backdrop-filter: blur(10px);
                border-right: 1px solid rgba(131, 56, 236, 0.2);
                z-index: 2;
            }}
            
            h1, h2, h3 {{ color: #ffffff !important; text-shadow: 0 0 20px rgba(131, 56, 236, 0.3); }}

            div[data-testid="metric-container"] {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(131, 56, 236, 0.2);
                backdrop-filter: blur(5px);
                border-radius: 10px;
                padding: 10px;
                transition: transform 0.3s ease;
            }}
            div[data-testid="metric-container"]:hover {{
                transform: translateY(-5px);
                border-color: #ff006e;
            }}
            
            span[data-baseweb="tag"] {{
                background-color: rgba(131, 56, 236, 0.3) !important;
                border: 1px solid rgba(131, 56, 236, 0.6);
            }}
        </style>
        <div id="particles-container">{particulas_html}</div>
    """, unsafe_allow_html=True)