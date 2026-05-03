from fastapi import FastAPI
import requests
import os
import time

app = FastAPI()

# ==============================
# CONFIG
# ==============================
BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

# ==============================
# TOKEN AUTOMÁTICO
# ==============================
access_token = None
token_expire = 0


def get_token():
    global access_token, token_expire

    if access_token and time.time() < token_expire:
        return access_token

    print("🔑 Gerando novo token...")

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )

    data = response.json()

    access_token = data["access_token"]
    token_expire = time.time() + data.get("expires_in", 3600) - 60

    print("✅ Token atualizado")

    return access_token


def headers():
    return {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    }


# ==============================
# PAGINAÇÃO GENÉRICA (RESOLVE 100%)
# ==============================
def fetch_all_pages(endpoint, params=None):
    pagina = 1
    tamanho = 100
    resultados = []

    while True:
        print(f"📄 Página {pagina} - {endpoint}")

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers(),
            params={**(params or {}), "pagina": pagina, "tamanho_pagina": tamanho},
        )

        data = response.json()

        # garante funcionamento independente da estrutura
        if isinstance(data, list):
            itens = data
        else:
            itens = data.get("itens", [])

        if not itens:
            break

        resultados.extend(itens)

        if len(itens) < tamanho:
            break

        pagina += 1

    return resultados


# ==============================
# ENDPOINTS
# ==============================

@app.get("/")
def home():
    return {"status": "ok"}


# ------------------------------
# CONTAS A RECEBER
# ------------------------------
@app.get("/contas-receber")
def contas_receber():
    dados = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"
    )
    return dados


# ------------------------------
# CONTAS A PAGAR
# ------------------------------
@app.get("/contas-pagar")
def contas_pagar():
    dados = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    )
    return dados


# ------------------------------
# CATEGORIAS
# ------------------------------
@app.get("/categorias")
def categorias():
    dados = fetch_all_pages("/v1/categorias")
    return {"itens": dados}


# ------------------------------
# CATEGORIAS DRE
# ------------------------------
@app.get("/categorias-dre")
def categorias_dre():
    response = requests.get(
        f"{BASE_URL}/v1/financeiro/categorias-dre",
        headers=headers()
    )
    return response.json()


# ------------------------------
# CONTA FINANCEIRA
# ------------------------------
@app.get("/conta-financeira")
def conta_financeira():
    dados = fetch_all_pages("/v1/conta-financeira")
    return {"itens": dados}


# ------------------------------
# BAIXAS (SIMPLES)
# ------------------------------
@app.get("/baixas")
def baixas():
    receber = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"
    )

    pagar = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    )

    todos = receber + pagar
    resultado = []

    for item in todos:
        try:
            parcela_id = item.get("id")

            if not parcela_id:
                continue

            url = f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{parcela_id}/baixa"

            response = requests.get(url, headers=headers())

            if response.status_code == 200:
                baixa = response.json()

                resultado.append({
                    "id": parcela_id,
                    "data_pagamento": baixa.get("data_pagamento"),
                    "valor": baixa.get("valor_composicao", {}).get("valor_bruto"),
                    "metodo_pagamento": baixa.get("metodo_pagamento"),
                })

        except Exception as e:
            continue

    return resultado