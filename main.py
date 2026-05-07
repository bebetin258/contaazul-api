import requests
import os
import psycopg
from datetime import datetime
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI

app = FastAPI()

# ==========================================
# CONFIG
# ==========================================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

API_BASE_URL = "https://api-v2.contaazul.com"
AUTH_URL = "https://auth.contaazul.com/oauth2/token"

ACCESS_TOKEN = None


# ==========================================
# DATABASE
# ==========================================
def get_connection():
    return psycopg.connect(DATABASE_URL)


def get_refresh_token():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT refresh_token FROM tokens WHERE id = 1")
            row = cur.fetchone()

            if not row:
                raise Exception("Refresh token não encontrado")

            return row[0]


def update_refresh_token(new_token):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tokens
                SET refresh_token = %s
                WHERE id = 1
                """,
                (new_token,)
            )
        conn.commit()


# ==========================================
# TOKEN
# ==========================================
def refresh_access_token():

    global ACCESS_TOKEN

    response = requests.post(
        AUTH_URL,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": get_refresh_token()
        },
        timeout=30
    )

    print("TOKEN STATUS:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Erro ao renovar token")

    data = response.json()

    ACCESS_TOKEN = data["access_token"]

    # salva novo refresh token
    if "refresh_token" in data:
        update_refresh_token(data["refresh_token"])

    return ACCESS_TOKEN


def get_headers():

    global ACCESS_TOKEN

    if not ACCESS_TOKEN:
        refresh_access_token()

    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }


# ==========================================
# CONTAS A RECEBER
# ==========================================
def buscar_contas_receber():

    todos = []

    pagina = 1

    while True:

        params = {
            "pagina": pagina,
            "tamanho_pagina": 100,

            # IMPORTANTE:
            # a Conta Azul precisa destes filtros
            "data_vencimento_de": "2020-01-01",
            "data_vencimento_ate": "2035-12-31"
        }

        response = requests.get(
            f"{API_BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
            headers=get_headers(),
            params=params,
            timeout=60
        )

        print("URL:", response.url)
        print("STATUS:", response.status_code)

        if response.status_code == 401:
            refresh_access_token()

            response = requests.get(
                f"{API_BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
                headers=get_headers(),
                params=params,
                timeout=60
            )

        if response.status_code != 200:
            print(response.text)
            break

        data = response.json()

        # DEBUG COMPLETO
        print("JSON:")
        print(data)

        # AQUI ESTÁ O PONTO CRÍTICO
        itens = data.get("itens", [])

        print(f"PÁGINA {pagina}")
        print(f"REGISTROS: {len(itens)}")

        if not itens:
            break

        todos.extend(itens)

        total_paginas = data.get("total_paginas", 1)

        print("TOTAL PAGINAS:", total_paginas)

        if pagina >= total_paginas:
            break

        pagina += 1

    print("TOTAL FINAL:", len(todos))

    return todos


# ==========================================
# ENDPOINT
# ==========================================
@app.get("/contas-receber")
def contas_receber():

    dados = buscar_contas_receber()

    return {
        "total": len(dados),
        "itens": dados
    }