import streamlit as st
import pandas as pd

# Sample data
data = {
    "topico": [1, 2, 3, 4, 5, 1, 2, 3, 1, 2, 3, 4],
    "status": [
        "Estudar",
        "Revisar",
        "Concluído",
        "Estudar",
        "Concluído",
        "Revisar",
        "Estudar",
        "Concluído",
        "Estudar",
        "Revisar",
        "Concluído",
        "Estudar",
    ],
    "materia": [
        "Matemática",
        "Matemática",
        "Matemática",
        "Matemática",
        "Matemática",
        "Biologia",
        "Biologia",
        "Biologia",
        "Matemática",
        "Matemática",
        "Matemática",
        "Matemática",
    ],
    "nivel": [
        "Básico",
        "Básico",
        "Básico",
        "Básico",
        "Básico",
        "Básico",
        "Básico",
        "Básico",
        "Avançado",
        "Avançado",
        "Avançado",
        "Avançado",
    ],
    "confiança": [
        "Baixa",
        "Média",
        "Alta",
        "Baixa",
        "Alta",
        "Média",
        "Baixa",
        "Alta",
        "Média",
        "Alta",
        "Baixa",
        "Média",
    ],
    "dificuldade": [
        "Fácil",
        "Média",
        "Difícil",
        "Fácil",
        "Difícil",
        "Média",
        "Fácil",
        "Difícil",
        "Média",
        "Difícil",
        "Fácil",
        "Média",
    ],
}

df = pd.DataFrame(data)


def calcular_progresso(df, groupby_cols):
    progresso = df.groupby(groupby_cols)["status"].value_counts().unstack(fill_value=0)
    progresso["Total"] = progresso.sum(axis=1)
    progresso["Concluído"] = progresso.get("Concluído", 0)
    progresso["Percentual Concluído"] = (
        (progresso["Concluído"] / progresso["Total"]) * 100
    ).astype(int)
    return progresso


st.title("Progresso das Matérias")

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"
    st.session_state.materia_selecionada = ""
    st.session_state.nivel_selecionado = ""

if st.session_state.pagina == "home":
    progresso_df = calcular_progresso(df, ["materia"])
    for materia, row in progresso_df.iterrows():
        st.subheader(materia)
        st.progress(row["Percentual Concluído"] / 100)
        st.write(f"{row['Concluído']}/{row['Total']}")
        if st.button(f"Ver detalhes - {materia}"):
            st.session_state.pagina = "detalhes"
            st.session_state.materia_selecionada = materia
            st.rerun()

elif st.session_state.pagina == "detalhes":
    materia = st.session_state.materia_selecionada
    st.subheader(f"Progresso detalhado - {materia}")
    progresso_nivel_df = calcular_progresso(df[df["materia"] == materia], ["nivel"])

    for nivel, row in progresso_nivel_df.iterrows():
        st.write(f"Nível: {nivel}")
        st.progress(row["Percentual Concluído"] / 100)
        st.write(f"{row['Concluído']}/{row['Total']}")
        if st.button(f"Ver detalhes - {nivel}"):
            st.session_state.nivel_selecionado = nivel
            st.session_state[f"detalhes_{nivel}"] = not st.session_state.get(
                f"detalhes_{nivel}", False
            )
            st.rerun()

        if st.session_state.get(f"detalhes_{nivel}", False):
            nivel_df = df[(df["materia"] == materia) & (df["nivel"] == nivel)]

            # Injecting CSS to change progress bar color to yellow
            st.markdown(
                """
                <style>
                    .stProgress > div > div > div > div {
                        background-color: yellow;
                    }
                </style>
                """,
                unsafe_allow_html=True,
            )

            st.write("### Distribuição de Status")
            status_counts = nivel_df["status"].value_counts(normalize=True) * 100
            for status, pct in status_counts.items():
                st.write(f"{status}: {int(pct)}%")
                st.progress(pct / 100)

            st.write("### Distribuição de Confiança")
            confianca_counts = nivel_df["confiança"].value_counts(normalize=True) * 100
            for confianca, pct in confianca_counts.items():
                st.write(f"{confianca}: {int(pct)}%")
                st.progress(pct / 100)

            st.write("### Distribuição de Dificuldade")
            dificuldade_counts = (
                nivel_df["dificuldade"].value_counts(normalize=True) * 100
            )
            for dificuldade, pct in dificuldade_counts.items():
                st.write(f"{dificuldade}: {int(pct)}%")
                st.progress(pct / 100)

            st.table(nivel_df[["topico", "status", "confiança", "dificuldade"]])

    if st.button("Voltar"):
        st.session_state.pagina = "home"
        st.rerun()
