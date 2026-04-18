from fastapi import FastAPI
import requests
import os
import json

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"

# =========================
# 📁 ARQUIVO DE TOKEN
# =========================
TOKEN_FILE = "token.json"


def salvar_token(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)


def carregar_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None


# =========================
# 🔑 GERAR ACCESS TOKEN
# =========================
def get_access_token():
    base64_auth = os.getenv("BASE64_AUTH")

    token_data = carregar_token()

    if not token_data:
        raise Exception("Sem refresh token salvo")

    refresh_token = token_data["refresh_token"]

    url = "https://auth.contaazul.com/oauth2/token"

    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("ERRO TOKEN:", response.text)
        raise Exception("Erro ao renovar token")

    novo = response.json()

    # 🔥 salva novo refresh token automaticamente
    if "refresh_token" in novo:
        salvar_token(novo)

    return novo["access_token"]


# =========================
# 🔄 PAGINAÇÃO REAL
# =========================
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

        if response.status_code != 200:
            print("ERRO API:", response.text)
            break

        data = response.json()

        items = data.get("items", [])

        if not items:
            break

        todos.extend(items)

        print(f"Página {pagina} - {len(items)} registros")

        if len(items) < tamanho:
            break

        pagina += 1

    print(f"TOTAL FINAL: {len(todos)}")

    return todos


# =========================
# 🌐 ENDPOINTS
# =========================
@app.get("/")
def home():
    return {"status": "API rodando 🚀"}


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