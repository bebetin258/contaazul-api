import os
import requests
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI

app = FastAPI()

# ==========================================
# CONFIG
# ==========================================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

API_BASE_URL = "https://api-v2.contaazul.com"
AUTH_URL = "https://auth.contaazul.com/oauth2/token"

ACCESS_TOKEN = None

TOKEN_FILE = "refresh_token.txt"


# ==========================================
# REFRESH TOKEN FILE
# ==========================================
def load_refresh_token():

    # tenta arquivo primeiro
    if os.path.exists(TOKEN_FILE):

        with open(TOKEN_FILE, "r") as f:

            token = f.read().strip()

            if token:
                return token

    raise Exception("refresh_token.txt não encontrado")


def save_refresh_token(token):

    with open(TOKEN_FILE, "w") as f:
        f.write(token)


# ==========================================
# TOKEN
# ==========================================
def refresh_access_token():

    global ACCESS_TOKEN

    refresh_token = load_refresh_token()

    response = requests.post(
        AUTH_URL,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        },
        timeout=30
    )

    print("TOKEN STATUS:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Erro ao renovar token")

    data = response.json()

    ACCESS_TOKEN = data["access_token"]

    # salva novo refresh token automaticamente
    novo_refresh = data.get("refresh_token")

    if novo_refresh:

        save_refresh_token(novo_refresh)

        print("NOVO REFRESH TOKEN SALVO")

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

        # token expirou
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
# CONTAS A PAGAR
# ==========================================
def buscar_contas_pagar():

    todos = []
    pagina = 1

    while True:

        params = {
            "pagina": pagina,
            "tamanho_pagina": 100,
            "data_vencimento_de": "2020-01-01",
            "data_vencimento_ate": "2035-12-31"
        }

        response = requests.get(
            f"{API_BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
            headers=get_headers(),
            params=params,
            timeout=60
        )

        print("URL:", response.url)
        print("STATUS:", response.status_code)

        # token expirou
        if response.status_code == 401:

            refresh_access_token()

            response = requests.get(
                f"{API_BASE_URL}/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
                headers=get_headers(),
                params=params,
                timeout=60
            )

        if response.status_code != 200:
            print(response.text)
            break

        data = response.json()

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
# ENDPOINTS
# ==========================================
@app.get("/contas-receber")
def contas_receber():

    dados = buscar_contas_receber()

    return {
        "total": len(dados),
        "itens": dados
    }


@app.get("/contas-pagar")
def contas_pagar():

    dados = buscar_contas_pagar()

    return {
        "total": len(dados),
        "itens": dados
    }