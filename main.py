import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import folium
from streamlit_folium import st_folium
from urllib.parse import urlparse, parse_qs

# Configuração da Página
st.set_page_config(page_title="Dashboard Streamlit", layout="wide")

# Simulação de Dados para 20 usuários
np.random.seed(42)
usuarios = {}
for i in range(1, 21):
    usuarios[str(i)] = pd.DataFrame(
        {
            "Data": pd.date_range(start="2024-01-01", periods=100),
            "Valor": np.random.randint(100, 500, 100),
            "Categoria": np.random.choice(["A", "B", "C"], size=100),
        }
    )

# Obter a Slug da URL
query_params = st.query_params.to_dict()
slug = query_params.get("slug", ["1"])[0]  # Padrão é 1 se não houver slug

df = usuarios.get(slug, usuarios["1"])  # Se a slug não existir, usa usuário 1

# Sidebar
st.sidebar.title("Opções do Dashboard")
st.sidebar.write(f"Usuário selecionado: {slug}")
option = st.sidebar.radio("Escolha um gráfico:", ["Resumo", "Gráficos", "Mapa"])


# Seção 1: Resumo
def show_summary():
    st.title(f"Resumo dos Dados - Usuário {slug}")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total de Registros", df.shape[0])
    col2.metric("Média dos Valores", f"R$ {df['Valor'].mean():.2f}")
    col3.metric("Valor Máximo", f"R$ {df['Valor'].max():.2f}")

    st.dataframe(df.head(10))


# Seção 2: Gráficos
def show_charts():
    st.title(f"Gráficos de Tendências - Usuário {slug}")

    fig, ax = plt.subplots(figsize=(10, 4))
    df.groupby("Data")["Valor"].sum().plot(ax=ax)
    ax.set_title("Tendência de Valores ao Longo do Tempo")
    ax.set_ylabel("Valor")
    st.pyplot(fig)

    st.subheader("Gráfico de Barras por Categoria")
    fig_bar = px.bar(
        df,
        x="Categoria",
        y="Valor",
        color="Categoria",
        title="Distribuição por Categoria",
    )
    st.plotly_chart(fig_bar)


# Seção 3: Mapa Interativo
def show_map():
    st.title(f"Mapa Interativo - Usuário {slug}")

    mapa = folium.Map(location=[-23.5505, -46.6333], zoom_start=5)
    folium.Marker([-23.5505, -46.6333], popup="São Paulo").add_to(mapa)
    folium.Marker([-22.9068, -43.1729], popup="Rio de Janeiro").add_to(mapa)

    st_folium(mapa, width=700, height=400)


# Exibir a página selecionada
if option == "Resumo":
    show_summary()
elif option == "Gráficos":
    show_charts()
elif option == "Mapa":
    show_map()
