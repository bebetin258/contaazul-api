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
# TOKEN BLINDADO
# =========================
def get_access_token():
    now = time.time()

    # ✅ CACHE (evita refresh toda hora)
    if ACCESS_TOKEN_CACHE["token"] and now < ACCESS_TOKEN_CACHE["expires_at"]:
        return ACCESS_TOKEN_CACHE["token"]

    conn = get_connection()
    cur = conn.cursor()

    # 🔒 LOCK → evita concorrência
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

        # 🔁 RETRY automático
        if response.status_code != 200:
            print("⚠️ Retry token...")
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
            raise Exception(f"Erro token: {response.text}")

        data = response.json()

        new_refresh = data["refresh_token"]
        access_token = data["access_token"]

        # 💾 salva novo refresh token
        cur.execute(
            "UPDATE tokens SET refresh_token = %s",
            (new_refresh,)
        )

        conn.commit()

        # 🧠 cache access token
        ACCESS_TOKEN_CACHE["token"] = access_token
        ACCESS_TOKEN_CACHE["expires_at"] = now + 3500

        return access_token

    finally:
        cur.close()
        conn.close()


# =========================
# PAGINAÇÃO
# =========================
def get_all_pages(endpoint):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    pagina = 1
    tamanho_pagina = 100
    todos = []

    while True:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params={
                "pagina": pagina,
                "tamanho_pagina": tamanho_pagina
            }
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

    return {
        "itens_totais": len(todos),
        "itens": todos
    }


# =========================
# ROTAS
# =========================

@app.get("/")
def home():
    return {"status": "API OK - v4 BLINDADA"}


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


@app.get("/contas-pagar")
def contas_pagar():
    token = get_access_token()

    response = requests.get(
        f"{BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )

    return response.json()


@app.get("/contas-receber")
def contas_receber():
    token = get_access_token()

    response = requests.get(
        f"{BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )

    return response.json()