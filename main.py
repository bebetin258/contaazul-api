from fastapi import FastAPI
import requests
import os
import json

app = FastAPI()

# ================================
# CONFIG
# ================================
BASE64 = "SEU_BASE64_AQUI"
TOKEN_FILE = "token.json"

# ================================
# SALVAR TOKEN
# ================================
def salvar_token(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

# ================================
# LER TOKEN
# ================================
def ler_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

# ================================
# GERAR NOVO TOKEN
# ================================
def gerar_token(refresh_token):
    url = "https://api-v2.contaazul.com/oauth2/token"

    headers = {
        "Authorization": f"Basic {BASE64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        raise Exception(f"Erro ao gerar token: {response.text}")

    novo_token = response.json()

    salvar_token(novo_token)

    return novo_token["access_token"]

# ================================
# OBTER ACCESS TOKEN (INTELIGENTE)
# ================================
def get_access_token():
    token_data = ler_token()

    if not token_data:
        raise Exception("token.json não encontrado")

    try:
        return gerar_token(token_data["refresh_token"])
    except:
        raise Exception("Refresh token expirado - gere manualmente")

# ================================
# PAGINAÇÃO
# ================================
def get_all_pages(endpoint):
    token = get_access_token()

    url = f"https://api-v2.contaazul.com{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    pagina = 1
    resultado = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        r = requests.get(url, headers=headers, params=params)

        if r.status_code != 200:
            raise Exception(f"Erro API: {r.text}")

        data = r.json()

        itens = data.get("items", [])

        if not itens:
            break

        resultado.extend(itens)

        pagina += 1

    return resultado

# ================================
# ENDPOINTS
# ================================
@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categories")