import os
import time
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

REFRESH_FILE = "refresh_token.txt"

# ======================================================
# TOKEN CACHE
# ======================================================

ACCESS_TOKEN = None
TOKEN_EXPIRES_AT = 0

# trava global
TOKEN_LOCK = threading.Lock()

# ======================================================
# REFRESH TOKEN
# ======================================================

def load_refresh_token():

    # 1 - tenta arquivo local
    if os.path.exists(REFRESH_FILE):

        with open(REFRESH_FILE, "r") as f:

            token = f.read().strip()

            if token:
                return token

    # 2 - fallback ENV do Render
    token_env = os.getenv("REFRESH_TOKEN")

    if token_env:
        return token_env

    raise Exception("Nenhum refresh token encontrado")


def save_refresh_token(token):

    with open(REFRESH_FILE, "w") as f:
        f.write(token)

# ======================================================
# REFRESH ACCESS TOKEN
# ======================================================

def refresh_access_token():

    global ACCESS_TOKEN
    global TOKEN_EXPIRES_AT

    with TOKEN_LOCK:

        # token ainda válido
        if ACCESS_TOKEN and time.time() < TOKEN_EXPIRES_AT:
            return ACCESS_TOKEN

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

            return None

        data = response.json()

        ACCESS_TOKEN = data["access_token"]

        expires_in = data.get("expires_in", 3600)

        # renova 5 min antes
        TOKEN_EXPIRES_AT = time.time() + expires_in - 300

        novo_refresh = data.get("refresh_token")

        if novo_refresh:

            save_refresh_token(novo_refresh)

            print("NOVO REFRESH TOKEN SALVO")

        return ACCESS_TOKEN

# ======================================================
# HEADERS
# ======================================================

def get_headers():

    token = refresh_access_token()

    if not token:

        raise Exception(
            "Refresh token inválido. "
            "Atualize REFRESH_TOKEN no Render."
        )

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

# ======================================================
# REQUEST SAFE
# ======================================================

def request_conta_azul(url, params=None):

    global ACCESS_TOKEN
    global TOKEN_EXPIRES_AT

    response = requests.get(
        url,
        headers=get_headers(),
        params=params,
        timeout=60
    )

    # token expirou inesperadamente
    if response.status_code == 401:

        print("TOKEN EXPIRADO - RENOVANDO")

        ACCESS_TOKEN = None
        TOKEN_EXPIRES_AT = 0

        token = refresh_access_token()

        if not token:

            return {
                "erro": "refresh token inválido"
            }

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=60
        )

    return response

# ======================================================
# PAGINAÇÃO
# ======================================================

def buscar_todos(endpoint):

    pagina = 1

    todos = []

    while True:

        params = {
            "pagina": pagina,
            "tamanho_pagina": 100,
            "data_vencimento_de": "2020-01-01",
            "data_vencimento_ate": "2035-12-31"
        }

        url = f"{API_BASE}{endpoint}"

        print(f"URL: {url}")
        print(f"PÁGINA: {pagina}")

        response = request_conta_azul(
            url,
            params=params
        )

        # erro token
        if isinstance(response, dict):
            return response

        print("STATUS:", response.status_code)

        if response.status_code != 200:

            print(response.text)

            break

        data = response.json()

        itens = data.get("itens", [])

        print("REGISTROS:", len(itens))

        if not itens:
            break

        todos.extend(itens)

        # última página
        if len(itens) < 100:
            break

        pagina += 1

    print("TOTAL FINAL:", len(todos))

    return {
        "total": len(todos),
        "itens": todos
    }

# ======================================================
# ROOT
# ======================================================

@app.get("/")
def root():

    return {
        "status": "online"
    }

# ======================================================
# CONTAS A PAGAR
# ======================================================

@app.get("/contas-pagar")
def contas_pagar():

    return buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    )

# ======================================================
# CONTAS A RECEBER
# ======================================================

@app.get("/contas-receber")
def contas_receber():

    return buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"
    )

# ======================================================
# CATEGORIAS DRE
# ======================================================

@app.get("/categorias-dre")
def categorias_dre():

    response = request_conta_azul(
        f"{API_BASE}/v1/categorias-dre"
    )

    # erro token
    if isinstance(response, dict):
        return response

    print("STATUS:", response.status_code)

    if response.status_code != 200:

        return {
            "erro": response.text
        }

    data = response.json()

    if isinstance(data, list):

        return {
            "total": len(data),
            "itens": data
        }

    return data