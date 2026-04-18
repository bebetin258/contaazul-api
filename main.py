from fastapi import FastAPI
import requests
import json
import os

app = FastAPI()

# =========================================
# 🔐 CONFIGURAÇÕES
# =========================================
BASE64 = "SEU_BASE64_AQUI"

TOKEN_FILE = "token.json"

# =========================================
# 💾 SALVAR TOKEN
# =========================================
def salvar_token(token_data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

# =========================================
# 📥 LER TOKEN
# =========================================
def ler_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

# =========================================
# 🔄 GERAR NOVO ACCESS TOKEN
# =========================================
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

    # 🔥 SALVA NOVO REFRESH TOKEN (IMPORTANTE)
    salvar_token(novo_token)

    return novo_token["access_token"]

# =========================================
# 🔑 OBTER ACCESS TOKEN
# =========================================
def get_access_token():
    token_data = ler_token()

    if not token_data:
        raise Exception("token.json não encontrado")

    return gerar_token(token_data["refresh_token"])

# =========================================
# 🔁 PAGINAÇÃO COMPLETA (CORRIGIDO)
# =========================================
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

        print(f"Buscando página {pagina}...")

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Erro API: {response.text}")

        data = response.json()

        # 🔍 DEBUG
        print(f"Resposta página {pagina}: {len(data.get('items', []))} registros")

        itens = data.get("items", [])

        resultado.extend(itens)

        # ✅ CONTROLE CORRETO
        total_paginas = data.get("total_paginas", 1)

        if pagina >= total_paginas:
            break

        pagina += 1

    print(f"Total final coletado: {len(resultado)} registros")

    return resultado

# =========================================
# 🌐 ENDPOINTS
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