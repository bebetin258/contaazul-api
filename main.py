import os
import threading
import requests

from fastapi import FastAPI
from requests.auth import HTTPBasicAuth

app = FastAPI()

# ======================================================
# CONFIG
# ======================================================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

API_BASE = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

TOKEN_FILE = "refresh_token.txt"

ACCESS_TOKEN = None

token_lock = threading.Lock()

# ======================================================
# REFRESH TOKEN
# ======================================================
def load_refresh_token():

    if not os.path.exists(TOKEN_FILE):
        raise Exception("Arquivo refresh_token.txt não encontrado")

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    if not token:
        raise Exception("Refresh token vazio")

    return token


def save_refresh_token(token):

    with open(TOKEN_FILE, "w") as f:
        f.write(token)


# ======================================================
# RENOVAR TOKEN
# ======================================================
def refresh_access_token():

    global ACCESS_TOKEN

    with token_lock:

        refresh_token = load_refresh_token()

        response = requests.post(
            TOKEN_URL,
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            timeout=30
        )

        print("TOKEN STATUS:", response.status_code)

        if response.status_code != 200:

            print(response.text)

            raise Exception("Erro ao renovar token")

        data = response.json()

        ACCESS_TOKEN = data["access_token"]

        novo_refresh = data.get("refresh_token")

        if novo_refresh:

            save_refresh_token(novo_refresh)

            print("NOVO REFRESH TOKEN SALVO")

        return ACCESS_TOKEN


# ======================================================
# HEADERS
# ======================================================
def get_headers():

    global ACCESS_TOKEN

    if not ACCESS_TOKEN:
        refresh_access_token()

    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }


# ======================================================
# REQUEST COM AUTO REFRESH
# ======================================================
def request_conta_azul(url, params=None):

    response = requests.get(
        url,
        headers=get_headers(),
        params=params,
        timeout=60
    )

    # TOKEN EXPIRADO
    if response.status_code == 401:

        print("TOKEN EXPIRADO - RENOVANDO")

        refresh_access_token()

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=60
        )

    return response


# ======================================================
# CONTAS A PAGAR
# ======================================================
@app.get("/contas-pagar")
def contas_pagar():

    todos = []

    pagina = 1

    while True:

        params = {
            "pagina": pagina,
            "tamanho_pagina": 100,
            "data_vencimento_de": "2020-01-01",
            "data_vencimento_ate": "2035-12-31"
        }

        response = request_conta_azul(
            f"{API_BASE}/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
            params=params
        )

        print("URL:", response.url)
        print("STATUS:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            break

        data = response.json()

        itens = data.get("itens", [])

        print(f"PÁGINA {pagina}")
        print(f"REGISTROS: {len(itens)}")

        if not itens:
            break

        todos.extend(itens)

        # ÚLTIMA PÁGINA
        if len(itens) < 100:
            break

        pagina += 1

    print("TOTAL FINAL:", len(todos))

    return {
        "total": len(todos),
        "itens": todos
    }


# ======================================================
# CONTAS A RECEBER
# ======================================================
@app.get("/contas-receber")
def contas_receber():

    todos = []

    pagina = 1

    while True:

        params = {
            "pagina": pagina,
            "tamanho_pagina": 100,
            "data_vencimento_de": "2020-01-01",
            "data_vencimento_ate": "2035-12-31"
        }

        response = request_conta_azul(
            f"{API_BASE}/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
            params=params
        )

        print("URL:", response.url)
        print("STATUS:", response.status_code)

        if response.status_code != 200:
            print(response.text)
            break

        data = response.json()

        itens = data.get("itens", [])

        print(f"PÁGINA {pagina}")
        print(f"REGISTROS: {len(itens)}")

        if not itens:
            break

        todos.extend(itens)

        # ÚLTIMA PÁGINA
        if len(itens) < 100:
            break

        pagina += 1

    print("TOTAL FINAL:", len(todos))

    return {
        "total": len(todos),
        "itens": todos
    }