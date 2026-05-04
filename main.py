import requests
import time
import os
import psycopg
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI

app = FastAPI()

# =========================
# CONFIG
# =========================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

API_BASE_URL = "https://api-v2.contaazul.com"
AUTH_URL = "https://auth.contaazul.com/oauth2/token"

# CACHE TOKEN
ACCESS_TOKEN = None
TOKEN_EXPIRATION = None


# =========================
# DB
# =========================
def get_connection():
    return psycopg.connect(DATABASE_URL)


def get_refresh_token():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT refresh_token FROM tokens WHERE id = 1;")
            result = cur.fetchone()

    if not result:
        raise Exception("❌ Nenhum refresh_token encontrado")

    return result[0]


def update_refresh_token(new_token):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE tokens
                SET refresh_token = %s
                WHERE id = 1
            """, (new_token,))
        conn.commit()


# =========================
# TOKEN
# =========================
def refresh_access_token():
    refresh_token = get_refresh_token()

    response = requests.post(
        AUTH_URL,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        },
        timeout=30
    )

    if response.status_code != 200:
        print(response.text)
        raise Exception("❌ Falha ao renovar token")

    data = response.json()

    global ACCESS_TOKEN, TOKEN_EXPIRATION

    ACCESS_TOKEN = data["access_token"]
    TOKEN_EXPIRATION = datetime.now() + timedelta(seconds=data["expires_in"] - 60)

    update_refresh_token(data["refresh_token"])

    print("🔐 Token atualizado")

    return ACCESS_TOKEN


def get_access_token():
    global ACCESS_TOKEN, TOKEN_EXPIRATION

    if ACCESS_TOKEN and TOKEN_EXPIRATION and datetime.now() < TOKEN_EXPIRATION:
        return ACCESS_TOKEN

    return refresh_access_token()


def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }


# =========================
# UTIL
# =========================
def extract_list(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v

    return []


# =========================
# PAGINAÇÃO ROBUSTA
# =========================
def fetch_all_pages(endpoint, params=None):
    if params is None:
        params = {}

    all_data = []
    page = 1
    page_size = 100

    while True:
        current_params = params.copy()
        current_params.update({
            "pagina": page,
            "tamanho_pagina": page_size
        })

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            params=current_params,
            timeout=30
        )

        # 🔄 refresh automático
        if response.status_code == 401:
            print("🔄 Token expirado...")
            refresh_access_token()

            response = requests.get(
                f"{API_BASE_URL}{endpoint}",
                headers=get_headers(),
                params=current_params,
                timeout=30
            )

        if response.status_code != 200:
            print(response.text)
            raise Exception("Erro na API")

        data = response.json()
        page_data = extract_list(data)

        if not page_data:
            print("📭 Fim dos dados")
            break

        all_data.extend(page_data)

        print(f"📄 Página {page}: {len(page_data)} registros")

        # 🔥 parada segura
        if len(page_data) < page_size:
            break

        page += 1
        time.sleep(0.2)

    print(f"📊 Total coletado: {len(all_data)}")

    return all_data


# =========================
# PARAM GLOBAL (AMPLIADO)
# =========================
DEFAULT_DATE_FILTER = {
    "data_vencimento_de": "2000-01-01",
    "data_vencimento_ate": "2100-12-31"
}


# =========================
# ENDPOINTS
# =========================
@app.get("/categorias")
def categorias():
    return {"itens": fetch_all_pages("/v1/categorias")}


@app.get("/categorias_dre")
def categorias_dre():
    return {"itens": fetch_all_pages("/v1/financeiro/categorias-dre")}


@app.get("/contas")
def contas():
    return {"itens": fetch_all_pages("/v1/conta-financeira")}


@app.get("/contas_receber")
def contas_receber():
    return {
        "itens": fetch_all_pages(
            "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
            DEFAULT_DATE_FILTER
        )
    }


@app.get("/contas_pagar")
def contas_pagar():
    return {
        "itens": fetch_all_pages(
            "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
            DEFAULT_DATE_FILTER
        )
    }


# =========================
# TESTE LOCAL
# =========================
def run():
    print("🚀 Testando...")
    data = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        DEFAULT_DATE_FILTER
    )
    print(len(data))


if __name__ == "__main__":
    run()