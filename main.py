import requests
import os
import psycopg
from datetime import datetime, timedelta
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

# CACHE
BAIXAS_CACHE = None
BAIXAS_CACHE_TIME = None
CACHE_TTL = 600

MAX_WORKERS = 10


# =========================
# DB
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
        },
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(response.text)

    data = response.json()

    ACCESS_TOKEN = data["access_token"]
    TOKEN_EXPIRATION = datetime.now() + timedelta(seconds=data["expires_in"] - 60)

    update_refresh_token(data["refresh_token"])

    return ACCESS_TOKEN


def get_access_token():
    if ACCESS_TOKEN and TOKEN_EXPIRATION and datetime.now() < TOKEN_EXPIRATION:
        return ACCESS_TOKEN
    return refresh_access_token()


def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }


# =========================
# PAGINAÇÃO (VERSÃO ESTÁVEL)
# =========================
def fetch_all_pages(endpoint):

    all_data = []
    page = 1

    while True:
        params = {
            "pagina": page,
            "tamanho_pagina": 100
        }

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            params=params,
            timeout=30
        )

        print("URL:", response.url)
        print("STATUS:", response.status_code)

        if response.status_code == 401:
            refresh_access_token()
            continue

        if response.status_code != 200:
            print("ERRO REAL:", response.text)
            break

        data = response.json()

        items = data.get("items", [])

        if not items:
            break

        all_data.extend(items)

        if len(items) < 100:
            break

        page += 1

    return all_data


# =========================
# BAIXAS
# =========================
def get_baixa_parcela(parcela_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{parcela_id}/baixa",
            headers=get_headers(),
            timeout=30
        )

        if response.status_code != 200:
            return []

        data = response.json()

        resultado = []

        for b in data:
            resultado.append({
                "id_parcela": parcela_id,
                "data_pagamento": b.get("data_pagamento"),
                "conta_financeira": b.get("conta_financeira"),
                "metodo_pagamento": b.get("metodo_pagamento")
            })

        return resultado

    except:
        return []


def get_all_baixas():
    global BAIXAS_CACHE, BAIXAS_CACHE_TIME

    if BAIXAS_CACHE and BAIXAS_CACHE_TIME:
        if (datetime.now() - BAIXAS_CACHE_TIME).seconds < CACHE_TTL:
            return BAIXAS_CACHE

    pagar = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")
    receber = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")

    print(f"PAGAR: {len(pagar)} | RECEBER: {len(receber)}")

    ids = [
        i.get("id")
        for i in pagar + receber
        if i.get("data_pagamento") is not None
    ]

    resultado = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(get_baixa_parcela, pid) for pid in ids]

        for future in as_completed(futures):
            resultado.extend(future.result())

    BAIXAS_CACHE = resultado
    BAIXAS_CACHE_TIME = datetime.now()

    print(f"💰 Total baixas: {len(resultado)}")

    return resultado


# =========================
# FINANCEIRO
# =========================
def get_financeiro():

    pagar = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")
    receber = fetch_all_pages("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")

    print(f"PAGAR: {len(pagar)} | RECEBER: {len(receber)}")

    baixas = get_all_baixas()
    mapa_baixas = {b["id_parcela"]: b for b in baixas}

    financeiro = []

    def transformar(item, tipo):

        nome = None

        if isinstance(item.get("fornecedor"), dict):
            nome = item["fornecedor"].get("nome")

        if isinstance(item.get("cliente"), dict):
            nome = item["cliente"].get("nome")

        baixa = mapa_baixas.get(item.get("id"))

        return {
            "id": item.get("id"),
            "tipo_evento_financeiro": tipo,
            "descricao": item.get("descricao"),
            "total": item.get("total"),
            "data_vencimento": item.get("data_vencimento"),
            "data_competencia": item.get("data_competencia"),

            "data_pagamento": (
                baixa["data_pagamento"] if baixa else item.get("data_pagamento")
            ),

            "conta_financeira": (
                baixa["conta_financeira"] if baixa else None
            ),

            "metodo_pagamento": (
                baixa["metodo_pagamento"] if baixa else None
            ),

            "fornecedor": nome,

            "categoria": (
                item.get("categorias")[0]["nome"]
                if item.get("categorias")
                else None
            ),

            "centro_custo": (
                item.get("centros_de_custo")[0]["nome"]
                if item.get("centros_de_custo")
                else None
            )
        }

    for item in pagar:
        financeiro.append(transformar(item, "DESPESA"))

    for item in receber:
        financeiro.append(transformar(item, "RECEITA"))

    return financeiro


# =========================
# ENDPOINTS
# =========================
@app.get("/financeiro")
def financeiro():
    return {"itens": get_financeiro()}


@app.get("/baixas")
def baixas():
    return {"itens": get_all_baixas()}