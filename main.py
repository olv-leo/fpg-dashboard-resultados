import streamlit as st
import pandas as pd
import psycopg2
import hashlib
import base64
import os
from cryptography.fernet import Fernet
import time
import traceback
from dotenv import load_dotenv

load_dotenv()

CHAVE_FIXA = os.getenv("CHAVE_FIXA")
CONCLUIDA = "CONCLUÍDA"
REVISAR = "REVISAR"
ESTUDAR = "ESTUDAR"

st.set_page_config(page_title="Sistema de Progresso", page_icon="📊", layout="wide")

try:
    chave = hashlib.sha256(CHAVE_FIXA.encode()).digest()
    cifra = Fernet(base64.urlsafe_b64encode(chave))
except Exception as e:
    st.error(f"Erro na inicialização do sistema de criptografia: {e}")
    cifra = None


# Função para descriptografar o email a partir da URL
def descriptografar_email(valor_criptografado):
    if cifra is None:
        st.error("Sistema de criptografia não inicializado corretamente.")
        return None

    try:
        st.info("Decodificando token de acesso...")
        texto_descriptografado = cifra.decrypt(valor_criptografado.encode()).decode()
        # O valor descriptografado contém email + string_fixa
        email = texto_descriptografado.replace(CHAVE_FIXA, "")
        st.success(f"Token decodificado com sucesso para: {email}")
        return email
    except Exception as e:
        st.error(f"Erro ao descriptografar token: {str(e)}")
        st.info("Detalhes técnicos para suporte:")
        st.code(traceback.format_exc())
        return None


def conectar_bd():
    try:
        with st.spinner("Conectando ao banco de dados..."):
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("USER"),
                password=os.getenv("PASSWORD"),
                host=os.getenv("HOST"),
                port="5432",
            )
            st.success("Conexão com banco de dados estabelecida!")
            return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        st.info("Detalhes técnicos para suporte:")
        st.code(traceback.format_exc())
        return None


def obter_dados_usuario(email):
    st.info(f"Buscando dados para o usuário: {email}")

    conn = conectar_bd()
    if conn:
        try:
            with st.spinner("Processando consulta..."):
                cursor = conn.cursor()
                query = f"""
                WITH tarefas_usuarios AS (
                    SELECT * FROM tarefas_usuarios
                ),

                usuario AS (
                    SELECT * FROM usuarios WHERE email = %s
                ),

                mapa_materias AS (
                    SELECT * FROM mapa_materias
                ),

                avaliacao_tarefas AS (
                    SELECT 
                        usuario.email AS email_usuario,
                        tarefas.codigo_tarefa,
                        mapa.codigo_nivel as nivel,
                        mapa.materia,
                        mapa.subgrupo AS descricao_tarefa,
                        CASE WHEN tarefas.dificuldade IS NULL THEN 'SEM DADOS' ELSE
                        CASE WHEN tarefas.dificuldade = 0 THEN 'FÁCIL' ELSE
                        CASE WHEN tarefas.dificuldade = 1 THEN 'MÉDIO' ELSE 
                        CASE WHEN tarefas.dificuldade = 2 THEN 'DIFÍCIL' END END END END AS dificuldade,
                        CASE WHEN tarefas.entendimento IS NULL THEN 'SEM DADOS' ELSE
                        CASE WHEN tarefas.entendimento = 0 THEN 'BAIXO' ELSE
                        CASE WHEN tarefas.entendimento = 1 THEN 'MÉDIO' ELSE 
                        CASE WHEN tarefas.entendimento = 2 THEN 'ALTO' END END END END AS entendimento,
                        CASE 
                            WHEN tarefas.flag_esta_concluida THEN '{CONCLUIDA}'
                            WHEN tarefas.codigo_tarefa IS NULL THEN '{ESTUDAR}' 
                            ELSE '{REVISAR}' 
                        END AS status,
                        usuario.tipo_usuario
                    FROM mapa_materias mapa
                    CROSS JOIN usuario 
                    LEFT JOIN tarefas_usuarios tarefas 
                        ON mapa.codigo_subgrupo = tarefas.codigo_subgrupo
                )

                SELECT * FROM avaliacao_tarefas

                """
                cursor.execute(query, (email,))
                resultados = cursor.fetchall()

                # Verificar se temos resultados
                if not resultados:
                    st.warning(f"Nenhum dado encontrado para o usuário {email}")
                    cursor.close()
                    conn.close()
                    return None, "Free"

                # Converter resultados para DataFrame
                df = pd.DataFrame(
                    resultados,
                    columns=[
                        "email_usuario",
                        "codigo_tarefa",
                        "nivel",
                        "materia",
                        "descricao_tarefa",
                        "dificuldade",
                        "entendimento",
                        "status",
                        "tipo_usuario",
                    ],
                )

                # Exibir quantidade de registros encontrados
                st.success(f"Encontrados {len(df)} registros para o usuário.")

                # Mapeamento de colunas para o formato esperado pelo aplicativo
                df = df.rename(
                    columns={
                        "codigo_tarefa": "topico",
                        "entendimento": "confianca",
                    }
                )

                # Extrair o tipo de usuário
                tipo_usuario = df["tipo_usuario"].iloc[0] if not df.empty else "Free"

                # Remover a coluna tipo_usuario do DataFrame principal
                df = df.drop("email_usuario", axis=1)
                df = df.drop("tipo_usuario", axis=1)

                cursor.close()
                conn.close()

                return df, tipo_usuario
        except Exception as e:
            st.error(f"Erro ao buscar dados do usuário: {str(e)}")
            st.info("Detalhes técnicos para suporte:")
            st.code(traceback.format_exc())
            if conn:
                conn.close()
            return None, "Free"
    return None, "Free"


# Função para calcular progresso
def calcular_progresso(df, groupby_cols):
    try:
        progresso = (
            df.groupby(groupby_cols)["status"].value_counts().unstack(fill_value=0)
        )
        progresso["Total"] = progresso.sum(axis=1)
        progresso["Concluído"] = progresso.get(CONCLUIDA, 0)
        progresso["Percentual Concluído"] = (
            (progresso["Concluído"] / progresso["Total"]) * 100
        ).astype(int)
        return progresso
    except Exception as e:
        st.error(f"Erro ao calcular progresso: {str(e)}")
        st.code(traceback.format_exc())
        # Retornar DataFrame vazio para evitar erros
        return pd.DataFrame()


# Obtém o valor criptografado da URL
def obter_email_da_url():
    # Para debug
    st.info("Obtendo parâmetros da URL...")

    # Obter a URL completa do Streamlit usando a API recomendada
    url_params = st.query_params

    # Se não houver parâmetros na URL, verificar se estamos em um caminho específico
    if not url_params or "token" not in url_params:
        st.info("Nenhum token encontrado nos parâmetros de URL, verificando caminho...")

        # No Streamlit Cloud, podemos acessar a URL completa através da variável de ambiente
        path = os.environ.get("STREAMLIT_SERVER_BASE_PATH", "")
        if path:
            # Exibir o caminho para debug
            st.info(f"Caminho da aplicação: {path}")

            # Extrair a parte do caminho após "app/"
            partes = path.split("app/")
            if len(partes) > 1:
                st.success(f"Token encontrado no caminho: {partes[1][:10]}...")
                return partes[1]
            else:
                st.warning("Nenhum token encontrado no caminho.")
                return None
        else:
            st.warning(
                "Variável de ambiente STREAMLIT_SERVER_BASE_PATH não disponível."
            )
            return None

    # Exibir o token encontrado (parcial, por segurança)
    token = url_params.get("token", "")
    if token:
        st.success(f"Token encontrado nos parâmetros de URL: {token[:10]}...")
    else:
        st.warning("Token vazio nos parâmetros de URL.")

    return token


# Configuração inicial da interface
def inicializar_interface():
    st.title("Progresso das Matérias")

    # Inicializar o estado da sessão
    if "pagina" not in st.session_state:
        st.session_state.pagina = "home"
        st.session_state.materia_selecionada = ""
        st.session_state.nivel_selecionado = ""
        st.session_state.autenticado = False
        st.session_state.email_usuario = None
        st.session_state.tipo_usuario = None
        st.session_state.df = None
        st.session_state.tentativa_auth = False


# Configuração da interface principal
inicializar_interface()

# Verificar autenticação
if not st.session_state.autenticado:
    st.write("### Autenticação do Sistema")

    # Mostrar caixa de informação sobre o acesso
    st.info(
        "Este aplicativo requer um token de acesso válido. O token deve estar na URL como '?token=...' ou no caminho como '/app/...'"
    )

    # Obter token da URL
    valor_criptografado = obter_email_da_url()

    # Se já tentamos autenticar antes e falhou, mostrar opção para tentar novamente
    if st.session_state.tentativa_auth and not valor_criptografado:
        if st.button("Tentar novamente"):
            st.session_state.tentativa_auth = False
            st.rerun()

        st.error("Nenhum token de acesso encontrado na URL.")
        st.markdown(
            """
        ### Como acessar o sistema:
        1. Você deve receber um link de acesso personalizado
        2. Use o link completo para acessar o sistema
        3. Se você digitou o endereço manualmente, verifique se incluiu o token
        """
        )
    elif valor_criptografado:
        st.session_state.tentativa_auth = True

        # Mostrar barra de progresso para indicar processamento
        progress_bar = st.progress(0)

        # Atualizando a barra de progresso
        for percent_complete in range(25):
            time.sleep(0.01)
            progress_bar.progress(percent_complete / 100)

        email = descriptografar_email(valor_criptografado)

        # Atualizando a barra de progresso
        for percent_complete in range(25, 50):
            time.sleep(0.01)
            progress_bar.progress(percent_complete / 100)

        if email:
            # Atualizando a barra de progresso
            for percent_complete in range(50, 75):
                time.sleep(0.01)
                progress_bar.progress(percent_complete / 100)

            df, tipo_usuario = obter_dados_usuario(email)

            # Atualizando a barra de progresso
            for percent_complete in range(75, 100):
                time.sleep(0.01)
                progress_bar.progress(percent_complete / 100)

            progress_bar.progress(1.0)

            if df is not None:
                st.session_state.autenticado = True
                st.session_state.email_usuario = email
                st.session_state.tipo_usuario = tipo_usuario
                st.session_state.df = df

                # Mostrar mensagem de sucesso e redirecionar
                st.success(f"Autenticação bem-sucedida para {email}!")
                st.info("Redirecionando para o painel principal...")
                time.sleep(1)  # Pequeno atraso para mostrar a mensagem
                st.rerun()
            else:
                st.error("Não foi possível obter os dados do usuário.")
                st.info(
                    """
                Isso pode ocorrer devido a:
                1. Problemas de conexão com o banco de dados
                2. O email não está cadastrado no sistema
                3. Erro interno do servidor
                
                Por favor, tente novamente ou entre em contato com o suporte.
                """
                )

                if st.button("Tentar novamente"):
                    st.session_state.tentativa_auth = False
                    st.rerun()
        else:
            st.error("Token inválido ou expirado.")
            st.info(
                """
            O token fornecido não pôde ser decodificado corretamente.
            Isso pode acontecer se:
            1. O link foi digitado incorretamente
            2. O token expirou
            3. O token foi modificado
            
            Por favor, solicite um novo link de acesso ou entre em contato com o suporte.
            """
            )

            if st.button("Tentar novamente"):
                st.session_state.tentativa_auth = False
                st.rerun()
    else:
        st.session_state.tentativa_auth = True
        st.warning("Por favor, acesse através de um link válido.")
        st.info(
            """
        ### Como acessar o sistema:
        1. Você deve receber um link de acesso personalizado
        2. Use o link completo para acessar o sistema
        3. Se você digitou o endereço manualmente, verifique se incluiu o token
        """
        )

# Se autenticado, mostrar o conteúdo do aplicativo
if st.session_state.autenticado:
    df = st.session_state.df

    # Mostrar informações do usuário na barra lateral
    st.sidebar.markdown(f"### Usuário: {st.session_state.email_usuario}")
    st.sidebar.markdown(f"**Tipo de conta:** {st.session_state.tipo_usuario}")

    if st.sidebar.button("Sair"):
        # Limpar a sessão
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Verificar se o usuário é Free e mostrar mensagem para recursos premium
    if st.session_state.tipo_usuario == "Free":
        st.warning(
            "Recurso exclusivo para membros Premium, adquira agora em [LINK](https://seu-link-premium.com)"
        )

    try:
        # Continuar com o aplicativo normal
        if st.session_state.pagina == "home":
            if df.empty:
                st.warning("Nenhum dado disponível para exibição.")
            else:
                try:
                    progresso_df = calcular_progresso(df, ["materia"])

                    if progresso_df.empty:
                        st.warning(
                            "Não foi possível calcular o progresso. Verifique se há dados suficientes."
                        )
                    else:
                        # Layout em colunas para melhor visualização
                        col1, col2 = st.columns(2)

                        materias = progresso_df.index.tolist()
                        for i, materia in enumerate(materias):
                            # Alternar entre colunas
                            with col1 if i % 2 == 0 else col2:
                                row = progresso_df.loc[materia]
                                with st.container():
                                    st.subheader(materia)
                                    st.progress(row["Percentual Concluído"] / 100)
                                    st.write(
                                        f"{row['Concluído']}/{row['Total']} ({row['Percentual Concluído']}%)"
                                    )
                                    if st.button(f"Detalhes de {materia}"):
                                        st.session_state.pagina = "detalhes"
                                        st.session_state.materia_selecionada = materia
                                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao exibir o progresso: {e}")
                    st.code(traceback.format_exc())

        elif st.session_state.pagina == "detalhes":
            materia = st.session_state.materia_selecionada
            st.subheader(f"Progresso detalhado - {materia}")

            # Botão para voltar para home
            if st.button("← Voltar para página inicial"):
                st.session_state.pagina = "home"
                st.rerun()

            try:
                # Filtrar para a matéria selecionada
                materia_df = df[df["materia"] == materia]

                if materia_df.empty:
                    st.warning(f"Nenhum dado disponível para a matéria {materia}.")
                else:
                    progresso_nivel_df = calcular_progresso(materia_df, ["nivel"])

                    if progresso_nivel_df.empty:
                        st.warning(
                            "Não foi possível calcular o progresso por nível. Verifique se há dados suficientes."
                        )
                    else:
                        # Aplicando CSS para a cor da barra de progresso
                        st.markdown(
                            """
                            <style>
                                .stProgress > div > div > div > div {
                                    background-color: #0cb087;
                                }
                            </style>
                            """,
                            unsafe_allow_html=True,
                        )

                        for nivel, row in progresso_nivel_df.iterrows():
                            with st.expander(
                                f"Nível: {nivel} - {row['Percentual Concluído']}% concluído",
                                expanded=False,
                            ):
                                st.progress(row["Percentual Concluído"] / 100)
                                st.write(f"{row['Concluído']}/{row['Total']}")

                                nivel_df = materia_df[materia_df["nivel"] == nivel]

                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write("### Distribuição de Status")
                                    status_counts = (
                                        nivel_df["status"].value_counts(normalize=True)
                                        * 100
                                    )
                                    for status, pct in status_counts.items():
                                        st.write(f"{status}: {int(pct)}%")
                                        st.progress(pct / 100)

                                with col2:
                                    st.write("### Distribuição de Confiança")
                                    confianca_counts = (
                                        nivel_df["confianca"].value_counts(
                                            normalize=True
                                        )
                                        * 100
                                    )
                                    for confianca, pct in confianca_counts.items():
                                        st.write(f"{confianca}: {int(pct)}%")
                                        st.progress(pct / 100)

                                st.write("### Distribuição de Dificuldade")
                                dificuldade_counts = (
                                    nivel_df["dificuldade"].value_counts(normalize=True)
                                    * 100
                                )
                                for dificuldade, pct in dificuldade_counts.items():
                                    st.write(f"{dificuldade}: {int(pct)}%")
                                    st.progress(pct / 100)

                                st.subheader("Detalhe das tarefas")
                                st.dataframe(
                                    nivel_df[
                                        [
                                            "nivel",
                                            "materia",
                                            "descricao_tarefa",
                                            "dificuldade",
                                            "confianca",
                                            "status",
                                        ]
                                    ],
                                    use_container_width=True,
                                )
            except Exception as e:
                st.error(f"Erro ao exibir detalhes: {e}")
                st.code(traceback.format_exc())
    except Exception as e:
        st.error(f"Erro inesperado no aplicativo: {e}")
        st.code(traceback.format_exc())

        st.warning("Ocorreu um erro inesperado. Tentando restaurar o aplicativo...")

        if st.button("Reiniciar aplicativo"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
