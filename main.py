import requests
import time
import os
import psycopg2

# =========================
# CONFIG
# =========================
BASE64_AUTH = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")

BASE_URL = "https://api-v2.contaazul.com"


# =========================
# DB (SUPABASE POSTGRES)
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_refresh_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens LIMIT 1;")
    token = cur.fetchone()[0]

    cur.close()
    conn.close()

    return token


def update_refresh_token(new_token):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tokens
        SET refresh_token = %s
    """, (new_token,))

    conn.commit()

    cur.close()
    conn.close()


# =========================
# TOKEN REFRESH
# =========================
def refresh_access_token():
    refresh_token = get_refresh_token()

    url = "https://api-v2.contaazul.com/oauth2/token"

    headers = {
        "Authorization": f"Basic {BASE64_AUTH}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        raise Exception(f"Erro ao atualizar token: {response.text}")

    data = response.json()

    new_access_token = data["access_token"]
    new_refresh_token = data["refresh_token"]

    update_refresh_token(new_refresh_token)

    return new_access_token


# =========================
# PAGINAÇÃO INTELIGENTE
# =========================
def extract_list(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v

    return []


def fetch_all_pages(endpoint, token, params=None):
    if params is None:
        params = {}

    all_data = []
    page = 1
    page_size = 100

    while True:
        params.update({
            "pagina": page,
            "tamanho_pagina": page_size
        })

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=params
        )

        if response.status_code == 401:
            print("🔄 Token expirado, renovando...")
            token = refresh_access_token()
            continue

        if response.status_code != 200:
            raise Exception(f"Erro API: {response.text}")

        data = response.json()
        page_data = extract_list(data)

        if not page_data:
            break

        all_data.extend(page_data)

        print(f"Página {page}: {len(page_data)} registros")

        if len(page_data) < page_size:
            break

        page += 1
        time.sleep(0.2)

    return all_data


# =========================
# EXECUÇÃO
# =========================
def run():
    token = refresh_access_token()

    endpoints = {
        "categorias": "/v1/categorias",
        "categorias_dre": "/v1/financeiro/categorias-dre",
        "contas": "/v1/conta-financeira",
        "contas_receber": "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        "contas_pagar": "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    }

    resultados = {}

    for nome, endpoint in endpoints.items():
        print(f"\n📊 Buscando: {nome}")

        params = {}

        if "buscar" in endpoint:
            params = {
                "data_vencimento_de": "2026-01-01",
                "data_vencimento_ate": "2026-12-31"
            }

        data = fetch_all_pages(endpoint, token, params)

        resultados[nome] = data
        print(f"✔ Total {nome}: {len(data)}")

    return resultados


if __name__ == "__main__":
    run()