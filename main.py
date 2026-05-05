import requests
import os
import psycopg
from datetime import datetime
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI()

# =========================
# CONFIG
# =========================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

API_BASE_URL = "https://api-v2.contaazul.com"
AUTH_URL = "https://auth.contaazul.com/oauth2/token"

ACCESS_TOKEN = None
TOKEN_EXPIRATION = None

MAX_WORKERS = 10


# =========================
# DB TOKEN
# =========================
def get_connection():
    return psycopg.connect(DATABASE_URL)


def get_refresh_token():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT refresh_token FROM tokens WHERE id = 1;")
            return cur.fetchone()[0]


def update_refresh_token(new_token):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE tokens SET refresh_token = %s WHERE id = 1", (new_token,))
        conn.commit()


# =========================
# TOKEN
# =========================
def refresh_access_token():
    global ACCESS_TOKEN, TOKEN_EXPIRATION

    response = requests.post(
        AUTH_URL,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": get_refresh_token()
        }
    )

    if response.status_code != 200:
        raise Exception(response.text)

    data = response.json()

    ACCESS_TOKEN = data["access_token"]
    TOKEN_EXPIRATION = datetime.now()

    update_refresh_token(data["refresh_token"])

    return ACCESS_TOKEN


def get_access_token():
    return ACCESS_TOKEN if ACCESS_TOKEN else refresh_access_token()


def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }


# =========================
# PAGINAÇÃO PADRÃO
# =========================
def fetch_all_pages(endpoint):

    all_data = []
    page = 1

    while True:
        params = {
            "pagina": page,
            "tamanho_pagina": 100,
            "data_vencimento_de": "2020-01-01",
            "data_vencimento_ate": datetime.today().strftime("%Y-%m-%d")
        }

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            params=params
        )

        if response.status_code == 401:
            refresh_access_token()
            continue

        if response.status_code != 200:
            print("ERRO:", response.text)
            break

        data = response.json()

        items = data.get("itens", [])
        total_paginas = data.get("total_paginas", 1)

        print(f"{endpoint} - PAGINA {page}/{total_paginas} - {len(items)} registros")

        if not items:
            break

        all_data.extend(items)

        if page >= total_paginas:
            break

        page += 1

    return all_data


# =========================
# ENDPOINTS BASE
# =========================
@app.get("/contas-pagar")
def contas_pagar():
    data = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")
    return {"itens": data}


@app.get("/contas-receber")
def contas_receber():
    data = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")
    return {"itens": data}


@app.get("/categorias")
def categorias():
    response = requests.get(
        f"{API_BASE_URL}/v1/categorias",
        headers=get_headers()
    )
    return response.json()


@app.get("/categorias-dre")
def categorias_dre():
    response = requests.get(
        f"{API_BASE_URL}/v1/categorias/dre",
        headers=get_headers()
    )
    return response.json()


@app.get("/contas-financeiras")
def contas_financeiras():
    response = requests.get(
        f"{API_BASE_URL}/v1/financeiro/contas-financeiras",
        headers=get_headers()
    )
    return response.json()


# =========================
# BAIXAS (PARALELO)
# =========================
def get_baixa(parcela_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{parcela_id}/baixa",
            headers=get_headers()
        )

        if response.status_code != 200:
            return []

        data = response.json()

        return [
            {
                "id_parcela": parcela_id,
                "id_baixa": b.get("id"),
                "data_pagamento": b.get("data_pagamento"),
                "valor_bruto": b.get("valor_composicao", {}).get("valor_bruto"),
                "juros": b.get("valor_composicao", {}).get("juros"),
                "multa": b.get("valor_composicao", {}).get("multa"),
                "desconto": b.get("valor_composicao", {}).get("desconto"),
                "metodo_pagamento": b.get("metodo_pagamento"),
                "tipo": b.get("tipo_evento_financeiro")
            }
            for b in data
        ]

    except:
        return []


@app.get("/baixas")
def baixas():

    pagar = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")
    receber = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")

    ids = [i.get("id") for i in pagar + receber]

    resultado = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(get_baixa, pid) for pid in ids]

        for future in as_completed(futures):
            resultado.extend(future.result())

    return {"itens": resultado}