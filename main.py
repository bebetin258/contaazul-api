from fastapi import FastAPI
import requests
import json
import os

app = FastAPI()

# =========================================
# 🔐 CONFIGURAÇÕES (ENV)
# =========================================
BASE64 = os.getenv("BASE64_AUTH")

if not BASE64:
    raise Exception("BASE64_AUTH não definido no ambiente")

TOKEN_FILE = "token.json"

# =========================================
# 📥 LER TOKEN
# =========================================
def ler_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

# =========================================
# 💾 SALVAR TOKEN
# =========================================
def salvar_token(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

# =========================================
# 🔄 GERAR ACCESS TOKEN (1x por requisição)
# =========================================
def gerar_token():
    token_data = ler_token()

    if not token_data or "refresh_token" not in token_data:
        raise Exception("token.json inválido ou ausente")

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

    novo_token = response.json()

    # 🔥 salva novo refresh_token (IMPORTANTE)
    salvar_token(novo_token)

    return novo_token["access_token"]

# =========================================
# 🌐 REQUEST API
# =========================================
def request_api(url, token, params=None):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Erro API: {response.text}")

    return response.json()

# =========================================
# 🔁 PAGINAÇÃO COMPLETA
# =========================================
def get_all_pages(endpoint):

    # 🔥 gera token UMA vez por chamada
    token = gerar_token()

    url = f"https://api-v2.contaazul.com{endpoint}"

    pagina = 1
    resultado = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        print(f"Buscando página {pagina}...")

        data = request_api(url, token, params)

        itens = data.get("items", [])

        resultado.extend(itens)

        total_paginas = data.get("total_paginas", 1)

        if pagina >= total_paginas:
            break

        pagina += 1

    print(f"Total coletado: {len(resultado)} registros")

    return resultado

# =========================================
# 🚀 ENDPOINTS
# =========================================
@app.get("/")
def home():
    return {"status": "API Conta Azul rodando 🚀"}

@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categories")

@app.get("/contas-financeiras")
def contas_financeiras():
    return get_all_pages("/v1/financial_accounts")

@app.get("/centro-custo")
def centro_custo():
    return get_all_pages("/v1/cost_centers")

@app.get("/contas-pagar")
def contas_pagar():
    return get_all_pages("/v1/payables")

@app.get("/contas-receber")
def contas_receber():
    return get_all_pages("/v1/receivables")