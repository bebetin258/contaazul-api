from fastapi import FastAPI
import requests
import os
import psycopg2

app = FastAPI()

# 🔥 VERSIONAMENTO
VERSION = "v5.0 - CONTAS RECEBER/PAGAR ESTAVEL"
print(f"🚀 SUBIU NOVA VERSÃO: {VERSION}")

# =========================
# CONFIG
# =========================
BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64 = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# BANCO
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_refresh_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens WHERE id = 1")
    token = cur.fetchone()

    cur.close()
    conn.close()

    if not token:
        raise Exception("Refresh token não encontrado")

    return token[0]


def update_refresh_token(new_token):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE tokens SET refresh_token = %s WHERE id = 1",
        (new_token,)
    )

    conn.commit()
    cur.close()
    conn.close()

    print("🔄 Refresh token atualizado")


# =========================
# TOKEN
# =========================
def get_access_token():
    refresh_token = get_refresh_token()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {BASE64}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )

    data = response.json()

    if response.status_code != 200:
        raise Exception(f"Erro ao gerar token: {data}")

    update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {
        "status": "API OK",
        "version": VERSION
    }


# =========================
# CONTAS A RECEBER
# =========================
@app.get("/contas-receber")
def contas_receber():

    token = get_access_token()

    pagina = 1
    resultado = []

    while True:

        response = requests.get(
            f"{BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "pagina": pagina,
                "tamanho_pagina": 100,
                "data_vencimento_de": "2023-01-01",
                "data_vencimento_ate": "2100-01-01"
            }
        )

        if response.status_code != 200:
            break

        data = response.json()
        itens = data.get("itens", [])

        if not itens:
            break

        resultado.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    return resultado


# =========================
# CONTAS A PAGAR
# =========================
@app.get("/contas-pagar")
def contas_pagar():

    token = get_access_token()

    pagina = 1
    resultado = []

    while True:

        response = requests.get(
            f"{BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "pagina": pagina,
                "tamanho_pagina": 100,
                "data_vencimento_de": "2023-01-01",
                "data_vencimento_ate": "2100-01-01"
            }
        )

        if response.status_code != 200:
            break

        data = response.json()
        itens = data.get("itens", [])

        if not itens:
            break

        resultado.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    return resultado


# =========================
# OUTROS ENDPOINTS
# =========================

@app.get("/categorias")
def categorias():
    token = get_access_token()
    return requests.get(
        f"{BASE_URL}/v1/categorias",
        headers={"Authorization": f"Bearer {token}"},
        params={"pagina": 1, "tamanho_pagina": 100}
    ).json()


@app.get("/centro-custo")
def centro_custo():
    token = get_access_token()
    return requests.get(
        f"{BASE_URL}/v1/centro-de-custo",
        headers={"Authorization": f"Bearer {token}"},
        params={"pagina": 1, "tamanho_pagina": 100}
    ).json()


@app.get("/contas-financeiras")
def contas_financeiras():
    token = get_access_token()
    return requests.get(
        f"{BASE_URL}/v1/conta-financeira",
        headers={"Authorization": f"Bearer {token}"}
    ).json()


@app.get("/categorias-dre")
def categorias_dre():
    token = get_access_token()
    return requests.get(
        f"{BASE_URL}/v1/financeiro/categorias-dre",
        headers={"Authorization": f"Bearer {token}"}
    ).json()