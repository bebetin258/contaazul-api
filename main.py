from fastapi import FastAPI
import requests
import os
import time
import base64

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
# TOKEN GLOBAL (CACHE)
# ==============================
access_token = None
token_expire = 0


# ==============================
# TOKEN CORRETO (REFRESH TOKEN)
# ==============================
def get_token():
    global access_token, token_expire

    if access_token and time.time() < token_expire:
        return access_token

    print("🔑 Gerando novo token...")

    # 🔥 AUTH CORRETO
    auth = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth.encode()).decode()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        },
        timeout=10
    )

    data = response.json()

    # 🔥 PROTEÇÃO CRÍTICA
    if "access_token" not in data:
        print("❌ ERRO AO GERAR TOKEN:", data)
        raise Exception("Falha ao gerar access_token")

    access_token = data["access_token"]
    token_expire = time.time() + data.get("expires_in", 3600) - 60

    print("✅ Token atualizado")

    return access_token


def get_headers():
    token = get_token()
    return {"Authorization": f"Bearer {token}"}


# ==============================
# PAGINAÇÃO (SEM ERRO DE LIST)
# ==============================
def fetch_all_pages(endpoint):
    pagina = 1
    tamanho = 100
    resultados = []

    while True:
        print(f"📄 Página {pagina} - {endpoint}")

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=get_headers(),
            params={
                "pagina": pagina,
                "tamanho_pagina": tamanho
            },
            timeout=20
        )

        if response.status_code != 200:
            print("❌ ERRO API:", response.text)
            break

        data = response.json()

        # 🔥 RESOLVE LIST VS DICT
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
        time.sleep(0.2)

    return resultados


# ==============================
# ENDPOINTS
# ==============================

@app.get("/")
def home():
    return {"status": "ok"}


@app.get("/contas-receber")
def contas_receber():
    return fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar"
    )


@app.get("/contas-pagar")
def contas_pagar():
    return fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    )


@app.get("/categorias")
def categorias():
    return {"itens": fetch_all_pages("/v1/categorias")}


@app.get("/categorias-dre")
def categorias_dre():
    response = requests.get(
        f"{BASE_URL}/v1/financeiro/categorias-dre",
        headers=get_headers()
    )
    return response.json()


@app.get("/conta-financeira")
def conta_financeira():
    return {"itens": fetch_all_pages("/v1/conta-financeira")}


# ==============================
# BAIXAS (SEPARADO)
# ==============================
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
        parcela_id = item.get("id")

        if not parcela_id:
            continue

        try:
            response = requests.get(
                f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{parcela_id}/baixa",
                headers=get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, dict):
                    resultado.append({
                        "id": parcela_id,
                        "data_pagamento": data.get("data_pagamento"),
                        "valor": data.get("valor_composicao", {}).get("valor_bruto"),
                        "metodo_pagamento": data.get("metodo_pagamento"),
                    })

        except:
            continue

    return resultado