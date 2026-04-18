from fastapi import FastAPI
import requests
import os
import time

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"

BASE64 = os.getenv("BASE64_AUTH")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

# =============================
# CACHE DO TOKEN
# =============================
TOKEN_CACHE = {
    "access_token": None,
    "expira_em": 0
}


# =============================
# GERAR ACCESS TOKEN
# =============================
def get_access_token():
    agora = time.time()

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

    print("STATUS TOKEN:", response.status_code)
    print("RESPOSTA TOKEN:", response.text)

    if response.status_code != 200:
        raise Exception("❌ Refresh token inválido")

    token_data = response.json()

    TOKEN_CACHE["access_token"] = token_data["access_token"]
    TOKEN_CACHE["expira_em"] = agora + 3500  # ~58 min

    return TOKEN_CACHE["access_token"]


# =============================
# PAGINAÇÃO + DEBUG
# =============================
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

        print("\n=============================")
        print(f"➡️ URL: {url}")

        response = requests.get(url, headers=headers)

        print("STATUS:", response.status_code)
        print("RAW RESPONSE:", response.text[:1000])

        # 🔁 Se token expirou
        if response.status_code == 401:
            print("🔁 Token expirado, renovando...")
            TOKEN_CACHE["access_token"] = None
            token = get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            continue

        if response.status_code != 200:
            print("❌ ERRO API:", response.text)
            break

        data = response.json()

        # 🔍 Debug estrutura
        if isinstance(data, dict):
            print("📦 JSON KEYS:", list(data.keys()))
        else:
            print("📦 JSON NÃO É DICT")

        # 🔥 Tratamento flexível
        items = None

        if isinstance(data, dict):
            if "items" in data:
                items = data["items"]
            elif "data" in data:
                items = data["data"]
            elif "results" in data:
                items = data["results"]
            elif "categorias" in data:
                items = data["categorias"]
            else:
                print("⚠️ Estrutura desconhecida, usando data direto")
                items = data
        else:
            items = data

        # força lista
        if isinstance(items, dict):
            items = [items]

        print(f"📊 Itens encontrados: {len(items) if items else 0}")

        if not items:
            break

        todos.extend(items)

        if len(items) < tamanho:
            break

        pagina += 1

    print(f"\n🎯 TOTAL FINAL: {len(todos)} registros\n")

    return todos


# =============================
# ENDPOINTS
# =============================

@app.get("/")
def home():
    return {"status": "API Conta Azul rodando 🚀"}


@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")


@app.get("/contas-financeiras")
def contas_financeiras():
    return get_all_pages("/v1/conta-financeira")


@app.get("/centro-custo")
def centro_custo():
    return get_all_pages("/v1/centro-custo")


@app.get("/contas-pagar")
def contas_pagar():
    return get_all_pages("/v1/contas-a-pagar")


@app.get("/contas-receber")
def contas_receber():
    return get_all_pages("/v1/contas-a-receber")