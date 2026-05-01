from fastapi import FastAPI
import requests
import os
import psycopg2

app = FastAPI()

# =========================
# CONFIG
# =========================
BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64_AUTH = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# BANCO
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_refresh_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens LIMIT 1")
    token = cur.fetchone()[0]

    cur.close()
    conn.close()

    return token


def update_refresh_token(new_token):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE tokens SET refresh_token = %s", (new_token,))
    conn.commit()

    cur.close()
    conn.close()


# =========================
# TOKEN
# =========================
def get_access_token():
    refresh_token = get_refresh_token()

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
        raise Exception(response.text)

    data = response.json()

    update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# PAGINAÇÃO GENÉRICA
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
    return {"status": "API OK"}


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