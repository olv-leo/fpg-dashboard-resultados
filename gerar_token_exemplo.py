import hashlib
import base64
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
CHAVE_FIXA = os.getenv("CHAVE_FIXA")

# Inicializar o sistema de criptografia
try:
    chave = hashlib.sha256(CHAVE_FIXA.encode()).digest()
    cifra = Fernet(base64.urlsafe_b64encode(chave))
except Exception as e:
    raise ValueError(f"Erro na inicialização do sistema de criptografia: {e}")


def gerar_token(email):
    """
    Gera um token criptografado para um e-mail usando a chave fixa.

    Parâmetros:
        email (str): E-mail do usuário.

    Retorna:
        str: Token criptografado.
    """
    try:
        if not email:
            raise ValueError("E-mail inválido.")

        # Concatenar o email com a chave fixa antes da criptografia
        texto_para_criptografar = email + CHAVE_FIXA

        # Criptografar o texto
        token = cifra.encrypt(texto_para_criptografar.encode()).decode()

        return token
    except Exception as e:
        raise ValueError(f"Erro ao gerar token: {e}")


# Exemplo de uso
email_exemplo = "olv.leo@outlook.com"
token_gerado = gerar_token(email_exemplo)
print(f"Token gerado: {token_gerado}")
