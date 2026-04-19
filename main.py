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

BASE64 = os.getenv("BASE64_AUTH")  # client_id:client_secret em base64
DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# CONEXÃO BANCO
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

    return token[0] if token else None


def update_refresh_token(new_token):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tokens
        SET refresh_token = %s
        WHERE id = 1
    """, (new_token,))

    conn.commit()
    cur.close()
    conn.close()


# =========================
# TOKEN AUTOMÁTICO
# =========================
def get_access_token():
    refresh_token = get_refresh_token()

    if not refresh_token:
        raise Exception("Refresh token não encontrado no banco")

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

    if response.status_code != 200:
        raise Exception(f"Erro ao renovar token: {response.text}")

    data = response.json()

    # ⚠️ MUITO IMPORTANTE: sempre salvar o novo refresh_token
    update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# PAGINAÇÃO COMPLETA
# =========================
def get_all_pages(endpoint):
    access_token = get_access_token()

    pagina = 1
    resultado_final = []

    while True:
        print(f"Buscando página {pagina}")

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            params={
                "pagina": pagina,
                "tamanho_pagina": 100
            }
        )

        if response.status_code != 200:
            raise Exception(f"Erro API: {response.text}")

        data = response.json()

        itens = data.get("items", [])

        if not itens:
            break

        resultado_final.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    return resultado_final


# =========================
# ENDPOINTS
# =========================
@app.get("/")
def home():
    return {"status": "API Conta Azul rodando 🚀"}


@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")


@app.get("/contas-financeiras")
def contas_financeiras():
    return get_all_pages("/v1/conta-financeira")


@app.get("/centro-custo")
def centro_custo():
    return get_all_pages("/v1/centro-custo")


@app.get("/contas-pagar")
def contas_pagar():
    return get_all_pages("/v1/contas-pagar")


@app.get("/contas-receber")
def contas_receber():
    return get_all_pages("/v1/contas-receber")