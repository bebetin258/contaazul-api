from fastapi import FastAPI
import requests
import json
import os

app = FastAPI()

# =========================================
# CONFIG
# =========================================
BASE64 = "SEU_BASE64_AQUI"
TOKEN_FILE = "token.json"

# =========================================
# TOKEN EM MEMÓRIA (CACHE)
# =========================================
ACCESS_TOKEN = None

# =========================================
# SALVAR TOKEN
# =========================================
def salvar_token(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

# =========================================
# LER TOKEN
# =========================================
def ler_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

# =========================================
# GERAR TOKEN NOVO
# =========================================
def gerar_token():
    global ACCESS_TOKEN

    token_data = ler_token()

    if not token_data:
        raise Exception("token.json não encontrado")

    url = "https://api-v2.contaazul.com/oauth2/token"

    headers = {
        "Authorization": f"Basic {BASE64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": token_data["refresh_token"]
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        raise Exception(f"Erro ao gerar token: {response.text}")

    novo = response.json()

    # 🔥 salva novo refresh_token
    salvar_token(novo)

    ACCESS_TOKEN = novo["access_token"]

    return ACCESS_TOKEN

# =========================================
# PEGAR TOKEN (COM CACHE)
# =========================================
def get_token():
    global ACCESS_TOKEN

    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    return gerar_token()

# =========================================
# REQUEST COM RETRY AUTOMÁTICO
# =========================================
def request_api(url, params=None):
    global ACCESS_TOKEN

    token = get_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(url, headers=headers, params=params)

    # 🔥 Se token expirou → renova automaticamente
    if r.status_code == 401:
        print("Token expirado, renovando...")

        token = gerar_token()

        headers["Authorization"] = f"Bearer {token}"

        r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        raise Exception(f"Erro API: {r.text}")

    return r.json()

# =========================================
# PAGINAÇÃO CORRETA
# =========================================
def get_all_pages(endpoint):
    url = f"https://api-v2.contaazul.com{endpoint}"

    pagina = 1
    resultado = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        print(f"Página {pagina}")

        data = request_api(url, params)

        itens = data.get("items", [])

        resultado.extend(itens)

        total_paginas = data.get("total_paginas", 1)

        if pagina >= total_paginas:
            break

        pagina += 1

    print(f"TOTAL: {len(resultado)}")

    return resultado

# =========================================
# ENDPOINTS
# =========================================
@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categories")

@app.get("/contas-financeiras")
def contas_financeiras():
    return get_all_pages("/v1/financial_accounts")

@app.get("/centro-custo")
def centro_custo():
    return get_all_pages("/v1/cost_centers")