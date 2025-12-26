# 📲 Tiktok and Youtube Shorts Analytics

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)

> **Projeto desenvolvido para a disciplina de Business Intelligence da Universidade Federal do Ceará (UFC).**

Este projeto é uma solução completa de **Engenharia e Análise de Dados**, que vai desde a modelagem de um Data Warehouse (DW) até a visualização avançada de dados sobre tendências de vídeos curtos (TikTok e YouTube Shorts).

### Acesse o Dashboard Online
➡️ **[Clique aqui para explorar o projeto ao vivo](https://tiktokandyoutubeshortsanalysis.streamlit.app/)**

---

## 🛠️ Tech Stack & Bibliotecas

Este projeto utilizou um conjunto robusto de ferramentas para extração, processamento, armazenamento e visualização:

![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/-Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Plotly](https://img.shields.io/badge/-Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/-Scikit_Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![SciPy](https://img.shields.io/badge/-SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/-BeautifulSoup-000000?style=for-the-badge&logo=beautifulsoup&logoColor=white)
![Aiven](https://img.shields.io/badge/-Aiven_Cloud-FF355E?style=for-the-badge&logo=aiven&logoColor=white)

*Outras libs essenciais: `pymysql`, `cryptography`, `requests`, `pytrends`.*

---

## A Jornada do Projeto

O desenvolvimento seguiu um pipeline rigoroso de BI, focado em transformar dados brutos em inteligência acionável.

### 1. Definição e Exploração
Escolhemos um dataset desafiador que simula tendências de 2025. A fase inicial consistiu em uma **Análise Exploratória de Dados (EDA)** para entender a distribuição de visualizações, engajamento e identificar inconsistências.

### 2. Modelagem do Data Warehouse (DW)
Abandonamos a estrutura de "tabelão" (flat file) e construímos um **Data Warehouse** robusto seguindo as formas normais e boas práticas de modelagem dimensional (Star Schema).
* **Fatos:** `fact_video`, `fact_google_trends`.
* **Dimensões:** `dim_country`, `dim_platform`, `dim_creator`, `dim_sound`, `dim_time`, etc.
* **Hospedagem em Nuvem:** O banco de dados MySQL foi hospedado na nuvem utilizando o **Aiven Console**, garantindo acessibilidade e persistência segura dos dados.

### 3. Enriquecimento via Web Scraping & Automação
Para trazer realidade aos dados simulados, implementamos scripts de **Web Scraping** (com `BeautifulSoup` e `Requests`) hospedados e versionados via **GitHub**.
* **Desafio Musical:** A coluna original de sons estava desatualizada ou genérica. Desenvolvemos uma automação que extraiu o **Top 200 Global Hits** (Spotify/TikTok) e manipulou programaticamente a coluna de sons do dataset, inserindo músicas virais reais (ex: "Espresso", "Gata Only") para enriquecer a análise de áudio.
* **Validação de Termos:** Utilizamos scraping para validar quais termos e hashtags estavam em alta, cruzando com o `pytrends` (Google Trends).

### 4. Inteligência Artificial e Visualização
A camada final foi construída em **Streamlit**. Não apenas exibimos gráficos, mas integramos um modelo de **Machine Learning (Random Forest)** para calcular, em tempo real, quais fatores (hora de postagem, duração, uso de emojis) mais influenciam a taxa de engajamento.

---

## Sobre o Dataset

**Fonte:** Kaggle (Simulado/Curado)
Este conjunto de dados reflete padrões realistas de tendências de vídeos curtos.
* **Plataformas:** YouTube Shorts e TikTok.
* **Cobertura:** +100 Países.
* **Período:** Janeiro a Agosto de 2025.
* **Métricas:** Visualizações, curtidas, comentários, compartilhamentos e atributos de metadados.

> *Os dados foram higienizados, normalizados e enriquecidos com informações externas obtidas via scraping.*

---

## Funcionalidades do Dashboard

O projeto é dividido em 6 abas estratégicas:

| Aba | Descrição |
| :--- | :--- |
| **🏠 Visão Geral** | KPIs macro (Total de Views, Likes), comparativo de volume entre plataformas e análise de distribuição de dados (Boxplots e Curvas de Tendência). |
| **⚙️ Fatores (IA)** | **Destaque do projeto.** Um modelo de ML roda em background para dizer *o que* causa o sucesso. Inclui análise de melhor horário e nicho. |
| **📝 Conteúdo** | Processamento de Linguagem Natural (NLP) para extrair palavras-chave dos títulos e o **Music Lab**, que analisa o impacto de usar Hits Virais vs. Músicas Comuns. |
| **🌍 Geográfico** | Mapa de calor interativo global mostrando a intensidade de consumo de vídeos por país e região. |
| **🔝 Top Virais** | Uma "Galeria da Fama" estilizada com os vídeos de maior performance e listagem detalhada dos dados. |
| **📈 Trends** | Integração com dados externos para validar se os termos do dataset correspondem às buscas reais no Google Trends. |

---

## Habilidades Desenvolvidas

Durante a execução deste projeto, a equipe desenvolveu competências chave em:

* **Engenharia de Dados:** Pipeline ETL, limpeza de dados e injeção de dados via scripts Python.
* **Modelagem de Banco de Dados:** Criação de esquemas relacionais (SGBD) e normalização de dados.
* **Cloud Computing:** Configuração e gerenciamento de banco de dados MySQL na nuvem (Aiven).
* **Web Scraping:** Extração de dados não estruturados da web para enriquecimento de dataset.
* **Data Science:** Aplicação de algoritmos de Regressão (Random Forest) para análise de importância de features.
* **Data Visualization:** Criação de dashboards interativos e storytelling com dados usando Streamlit e Plotly.

---

## 👨‍💻 Autor

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0e75b6?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/jaimejrs/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/jaimejrs)
[![Medium](https://img.shields.io/badge/Medium-000000?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@jaimejrs)
