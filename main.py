from fastapi import FastAPI
import requests
import os
import time

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"

# 🔑 ENV
BASE64 = os.getenv("BASE64_AUTH")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

# 🧠 CACHE EM MEMÓRIA
TOKEN_CACHE = {
    "access_token": None,
    "expira_em": 0
}


def get_access_token():
    agora = time.time()

    # ✅ usa cache
    if TOKEN_CACHE["access_token"] and agora < TOKEN_CACHE["expira_em"]:
        return TOKEN_CACHE["access_token"]

    print("🔄 Gerando novo token...")

    url = "https://auth.contaazul.com/oauth2/token"

    headers = {
        "Authorization": f"Basic {BASE64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("❌ ERRO TOKEN:", response.text)
        raise Exception("Refresh token inválido")

    token_data = response.json()

    TOKEN_CACHE["access_token"] = token_data["access_token"]
    TOKEN_CACHE["expira_em"] = agora + 3500  # ~58 min

    return TOKEN_CACHE["access_token"]


def get_all_pages(endpoint):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    pagina = 1
    tamanho = 100
    todos = []

    while True:
        url = f"{BASE_URL}{endpoint}?pagina={pagina}&tamanho_pagina={tamanho}"

        response = requests.get(url, headers=headers)

        # 🔁 se token expirou no meio
        if response.status_code == 401:
            print("🔁 Token expirou, renovando...")
            TOKEN_CACHE["access_token"] = None
            token = get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            continue

        if response.status_code != 200:
            print("❌ ERRO API:", response.text)
            break

        data = response.json()
        items = data.get("items", [])

        if not items:
            break

        todos.extend(items)

        if len(items) < tamanho:
            break

        pagina += 1

    return todos


# ======================
# ENDPOINTS
# ======================

@app.get("/")
def home():
    return {"status": "API rodando 🚀"}


@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")


@app.get("/contas-financeiras")
def contas():
    return get_all_pages("/v1/conta-financeira")


@app.get("/centro-custo")
def centro():
    return get_all_pages("/v1/centro-custo")


@app.get("/contas-pagar")
def pagar():
    return get_all_pages("/v1/contas-a-pagar")


@app.get("/contas-receber")
def receber():
    return get_all_pages("/v1/contas-a-receber")