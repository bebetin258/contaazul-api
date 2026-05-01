from fastapi import FastAPI
import requests
import os
import psycopg2
import time
import threading

app = FastAPI()

VERSION = "v13.0 - TOKEN ESTAVEL FINAL"
print(f"🚀 SUBIU: {VERSION}")

BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64 = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# CACHE + LOCK (CRÍTICO)
# =========================
token_lock = threading.Lock()

access_token_cache = {
    "token": None,
    "expires_at": 0
}


# =========================
# BANCO
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_refresh_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens WHERE id = 1")
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        raise Exception("Refresh token não encontrado")

    return row[0]


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


# =========================
# TOKEN (BLINDADO)
# =========================
def get_access_token():
    with token_lock:

        now = time.time()

        # ✔ usa cache se ainda válido
        if access_token_cache["token"] and now < access_token_cache["expires_at"]:
            return access_token_cache["token"]

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
            print("❌ ERRO TOKEN:", data)
            raise Exception(data)

        # 🔥 atualiza refresh token
        update_refresh_token(data["refresh_token"])

        # 🔥 atualiza cache
        access_token_cache["token"] = data["access_token"]
        access_token_cache["expires_at"] = now + data.get("expires_in", 3600) - 60

        return access_token_cache["token"]


# =========================
# PAGINAÇÃO PADRÃO
# =========================
def buscar_todos(endpoint, params):
    token = get_access_token()

    pagina = 1
    resultado = []

    while True:
        params["pagina"] = pagina

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )

        if response.status_code != 200:
            print("Erro API:", response.text)
            break

        data = response.json()
        itens = data.get("itens", [])

        if not itens:
            break

        resultado.extend(itens)

        if len(itens) < params.get("tamanho_pagina", 100):
            break

        pagina += 1

    return resultado


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def home():
    return {"status": "ok", "version": VERSION}


@app.get("/contas-pagar")
def contas_pagar():
    return buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "tamanho_pagina": 100,
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )


@app.get("/contas-receber")
def contas_receber():
    return buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "tamanho_pagina": 100,
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )


# 🔥 BAIXA INDIVIDUAL (SEPARADO)
@app.get("/baixa/{parcela_id}")
def baixa(parcela_id: str):
    token = get_access_token()

    response = requests.get(
        f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{parcela_id}/baixa",
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()


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


@app.get("/categorias")
def categorias():
    token = get_access_token()

    return requests.get(
        f"{BASE_URL}/v1/categorias",
        headers={"Authorization": f"Bearer {token}"}
    ).json()