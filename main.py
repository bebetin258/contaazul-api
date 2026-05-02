from fastapi import FastAPI
import requests
import os
import psycopg2
import time

app = FastAPI()

# =========================
# CONFIG
# =========================
BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64_AUTH = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# CACHE TOKEN
# =========================
ACCESS_TOKEN_CACHE = {
    "token": None,
    "expires_at": 0
}

# =========================
# BANCO
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)

# =========================
# TOKEN
# =========================
def get_access_token():
    now = time.time()

    if ACCESS_TOKEN_CACHE["token"] and now < ACCESS_TOKEN_CACHE["expires_at"]:
        return ACCESS_TOKEN_CACHE["token"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens LIMIT 1 FOR UPDATE")
    refresh_token = cur.fetchone()[0]

    try:
        response = requests.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {BASE64_AUTH}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )

        if response.status_code != 200:
            conn.rollback()
            raise Exception(response.text)

        data = response.json()

        cur.execute(
            "UPDATE tokens SET refresh_token = %s",
            (data["refresh_token"],)
        )

        conn.commit()

        ACCESS_TOKEN_CACHE["token"] = data["access_token"]
        ACCESS_TOKEN_CACHE["expires_at"] = now + 3500

        return data["access_token"]

    finally:
        cur.close()
        conn.close()


# =========================
# PAGINAÇÃO REAL
# =========================
def get_all_pages(endpoint, params_extra=None):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    pagina = 1
    tamanho_pagina = 100
    todos = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": tamanho_pagina,
            **(params_extra or {})
        }

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            return {"erro": response.text}

        data = response.json()
        itens = data.get("itens", [])

        if not itens:
            break

        todos.extend(itens)

        if len(itens) < tamanho_pagina:
            break

        pagina += 1

    return {"itens": todos}


# =========================
# ROTAS
# =========================

@app.get("/")
def home():
    return {"status": "API OK - PAGINACAO REAL + BAIXAS"}


@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")


@app.get("/conta-financeira")
def conta_financeira():
    return get_all_pages("/v1/conta-financeira")


@app.get("/categorias-dre")
def categorias_dre():
    token = get_access_token()

    response = requests.get(
        f"{BASE_URL}/v1/financeiro/categorias-dre",
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()


@app.get("/contas-receber")
def contas_receber():
    return get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )


@app.get("/contas-pagar")
def contas_pagar():
    return get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )


# =========================
# 🔥 ENDPOINT BAIXAS
# =========================
@app.get("/baixas")
def baixas():
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    receber = get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )["itens"]

    pagar = get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )["itens"]

    ids = [x["id"] for x in receber + pagar]

    resultado = []

    for id_parcela in ids:
        response = requests.get(
            f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{id_parcela}/baixa",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            data["id_origem"] = id_parcela
            resultado.append(data)

    return {"itens": resultado}