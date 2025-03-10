import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Configuração da Página
st.set_page_config(page_title="Dashboard Streamlit", layout="wide")

# Simulação de Dados
df = pd.DataFrame(
    {
        "Data": pd.date_range(start="2024-01-01", periods=100),
        "Valor": np.random.randint(100, 500, 100),
    }
)

df["Categoria"] = np.random.choice(["A", "B", "C"], size=len(df))

# Sidebar
st.sidebar.title("Opções do Dashboard")
option = st.sidebar.radio("Escolha um gráfico:", ["Resumo", "Gráficos", "Mapa"])


# Seção 1: Resumo
def show_summary():
    st.title("Resumo dos Dados")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total de Registros", df.shape[0])
    col2.metric("Média dos Valores", f"R$ {df['Valor'].mean():.2f}")
    col3.metric("Valor Máximo", f"R$ {df['Valor'].max():.2f}")

    st.dataframe(df.head(10))


# Seção 2: Gráficos
def show_charts():
    st.title("Gráficos de Tendências")

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
    st.title("Mapa Interativo")

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
