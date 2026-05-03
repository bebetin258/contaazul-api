import requests
import time
import os
import psycopg
from requests.auth import HTTPBasicAuth

# =========================
# CONFIG
# =========================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

BASE_URL = "https://api-v2.contaazul.com"

TIMEOUT = 30
RETRY = 3


# =========================
# DB CONNECTION
# =========================
def get_connection():
    return psycopg.connect(DATABASE_URL)


# =========================
# TOKEN (DB)
# =========================
def get_refresh_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens WHERE id = 1;")
    result = cur.fetchone()

    cur.close()
    conn.close()

    if not result:
        raise Exception("❌ Nenhum refresh_token encontrado")

    return result[0]


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
# TOKEN REFRESH
# =========================
def refresh_access_token():
    refresh_token = get_refresh_token()

    url = f"{BASE_URL}/oauth2/token"

    payload = f"grant_type=refresh_token&refresh_token={refresh_token}"

    for attempt in range(RETRY):
        try:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data=payload,
                timeout=TIMEOUT
            )

            print(f"🔄 Tentativa {attempt+1} - Status: {response.status_code}")
            print("📨 Resposta:", response.text)

            if response.status_code != 200:
                raise Exception(response.text)

            data = response.json()

            new_access_token = data["access_token"]
            new_refresh_token = data["refresh_token"]

            update_refresh_token(new_refresh_token)

            print("🔐 Token atualizado com sucesso")

            return new_access_token

        except Exception as e:
            print(f"❌ Erro ao atualizar token: {e}")
            time.sleep(2)

    raise Exception("❌ Falha ao renovar token")


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
# REQUEST COM RETRY
# =========================
def make_request(url, headers, params):
    for attempt in range(RETRY):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=TIMEOUT
            )

            if response.status_code in [200, 401]:
                return response

            raise Exception(response.text)

        except Exception as e:
            print(f"❌ Erro request (tentativa {attempt+1}): {e}")
            time.sleep(2)

    raise Exception("❌ Falha na requisição")


# =========================
# PAGINAÇÃO
# =========================
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

        response = make_request(
            f"{BASE_URL}{endpoint}",
            headers,
            params
        )

        if response.status_code == 401:
            print("🔄 Token expirado, renovando...")
            token = refresh_access_token()
            continue

        data = response.json()
        page_data = extract_list(data)

        if not page_data:
            break

        all_data.extend(page_data)

        print(f"📄 Página {page}: {len(page_data)} registros")

        if len(page_data) < page_size:
            break

        page += 1
        time.sleep(0.2)

    return all_data


# =========================
# EXECUÇÃO
# =========================
def run():
    print("🚀 Iniciando execução...")

    token = refresh_access_token()

    endpoints = {
        "categorias": "/v1/categorias",
        "categorias_dre": "/v1/financeiro/categorias-dre",
        "contas": "/v1/conta-financeira",
        "contas_receber": "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        "contas_pagar": "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar"
    }

    for nome, endpoint in endpoints.items():
        print(f"\n📊 Buscando: {nome}")

        params = {}

        if "buscar" in endpoint:
            params = {
                "data_vencimento_de": "2026-01-01",
                "data_vencimento_ate": "2026-12-31"
            }

        data = fetch_all_pages(endpoint, token, params)

        print(f"✔ Total {nome}: {len(data)}")

    print("\n✅ Execução finalizada com sucesso")


# =========================
# START
# =========================
if __name__ == "__main__":
    run()