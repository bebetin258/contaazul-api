from fastapi import FastAPI
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

import requests
import os
import time
import threading

load_dotenv()

app = FastAPI()

# =========================
# CONFIG
# =========================

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

API_BASE = "https://api-v2.contaazul.com"

TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

# =========================
# TOKEN CACHE
# =========================

ACCESS_TOKEN = None
TOKEN_EXPIRES_AT = 0

# trava global
TOKEN_LOCK = threading.Lock()

# =========================
# REFRESH TOKEN FILE
# =========================

REFRESH_FILE = "refresh_token.txt"

def load_refresh_token():

    with open(REFRESH_FILE, "r") as f:
        return f.read().strip()

def save_refresh_token(token):

    with open(REFRESH_FILE, "w") as f:
        f.write(token)

# =========================
# REFRESH TOKEN
# =========================

def refresh_access_token():

    global ACCESS_TOKEN
    global TOKEN_EXPIRES_AT

    with TOKEN_LOCK:

        # outro endpoint já renovou
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

            raise Exception("Erro ao renovar token")

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

# =========================
# HEADERS
# =========================

def get_headers():

    token = refresh_access_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

# =========================
# REQUEST SAFE
# =========================

def request_conta_azul(url, params=None):

    response = requests.get(
        url,
        headers=get_headers(),
        params=params,
        timeout=60
    )

    # token expirou inesperadamente
    if response.status_code == 401:

        global ACCESS_TOKEN

        ACCESS_TOKEN = None

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=60
        )

    response.raise_for_status()

    return response.json()

# =========================
# PAGINAÇÃO
# =========================

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

        itens = (
            response.get("itens")
            or response.get("data")
            or []
        )

        print("REGISTROS:", len(itens))

        if not itens:
            break

        todos.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    print("TOTAL FINAL:", len(todos))

    return {"itens": todos}

# =========================
# ENDPOINTS
# =========================

@app.get("/contas-pagar")
def contas_pagar():

    return buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    )

@app.get("/contas-receber")
def contas_receber():

    return buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"
    )

@app.get("/categorias")
def categorias():

    return request_conta_azul(
        f"{API_BASE}/v1/categorias"
    )

@app.get("/categorias-dre")
def categorias_dre():

    return request_conta_azul(
        f"{API_BASE}/v1/categorias-dre"
    )

@app.get("/contas-financeiras")
def contas_financeiras():

    return request_conta_azul(
        f"{API_BASE}/v1/contas-financeiras"
    )