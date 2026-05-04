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

ACCESS_TOKEN = None
TOKEN_EXPIRATION = None


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
        headers={"Content-Type": "application/x-www-form-urlencoded"},
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

    print("🔐 Token atualizado")
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
# PAGINAÇÃO
# =========================
def fetch_all_pages(endpoint, params=None):
    if params is None:
        params = {}

    all_data = []
    page = 1

    while True:
        current_params = params.copy()
        current_params.update({
            "pagina": page,
            "tamanho_pagina": 100
        })

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            params=current_params,
            timeout=30
        )

        if response.status_code == 401:
            refresh_access_token()
            continue

        if response.status_code != 200:
            print(response.text)
            break

        data = response.json()

        lista = data if isinstance(data, list) else next(
            (v for v in data.values() if isinstance(v, list)), []
        )

        if not lista:
            break

        all_data.extend(lista)

        if len(lista) < 100:
            break

        page += 1
        time.sleep(0.2)

    return all_data


# =========================
# FINANCEIRO (FLATTEN)
# =========================
def get_financeiro():
    filtro = {
        "data_vencimento_de": "2000-01-01",
        "data_vencimento_ate": "2100-12-31"
    }

    pagar = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        filtro
    )

    receber = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        filtro
    )

    financeiro = []

    def transformar(item, tipo):
        return {
            "id": item.get("id"),
            "tipo": tipo,
            "descricao": item.get("descricao"),
            "total": item.get("total"),
            "data_vencimento": item.get("data_vencimento"),
            "data_competencia": item.get("data_competencia"),
            "fornecedor": (
                item.get("fornecedor", {}).get("nome")
                if isinstance(item.get("fornecedor"), dict)
                else None
            ),
            "categoria": (
                item.get("categorias")[0]["nome"]
                if item.get("categorias")
                else None
            ),
            "centro_custo": (
                item.get("centros_de_custo")[0]["nome"]
                if item.get("centros_de_custo")
                else None
            ),
            "atualizado_em": item.get("atualizado_em")
        }

    for item in pagar:
        financeiro.append(transformar(item, "DESPESA"))

    for item in receber:
        financeiro.append(transformar(item, "RECEITA"))

    return financeiro


# =========================
# BAIXAS (FLATTEN)
# =========================
def get_baixa_parcela(parcela_id):
    response = requests.get(
        f"{API_BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{parcela_id}/baixa",
        headers=get_headers(),
        timeout=30
    )

    if response.status_code == 404:
        return []

    if response.status_code == 401:
        refresh_access_token()
        return get_baixa_parcela(parcela_id)

    if response.status_code != 200:
        print(f"Erro {parcela_id}: {response.text}")
        return []

    return response.json()


def get_all_baixas():
    filtro = {
        "data_vencimento_de": "2000-01-01",
        "data_vencimento_ate": "2100-12-31"
    }

    pagar = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        filtro
    )

    receber = fetch_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        filtro
    )

    ids = set()

    for item in pagar:
        ids.add(item.get("id"))

    for item in receber:
        ids.add(item.get("id"))

    print(f"🔎 Total parcelas: {len(ids)}")

    resultado = []

    for i, parcela_id in enumerate(ids):
        print(f"📌 {i+1}/{len(ids)}")

        baixas = get_baixa_parcela(parcela_id)

        for b in baixas:
            resultado.append({
                "id_parcela": parcela_id,
                "id_baixa": b.get("id"),
                "data_pagamento": b.get("data_pagamento"),
                "valor_bruto": b.get("valor_composicao", {}).get("valor_bruto"),
                "juros": b.get("valor_composicao", {}).get("juros"),
                "multa": b.get("valor_composicao", {}).get("multa"),
                "desconto": b.get("valor_composicao", {}).get("desconto"),
                "metodo_pagamento": b.get("metodo_pagamento"),
                "tipo": b.get("tipo_evento_financeiro")
            })

        time.sleep(0.1)

    print(f"💰 Total baixas: {len(resultado)}")

    return resultado


# =========================
# ENDPOINTS
# =========================
@app.get("/financeiro")
def financeiro():
    return {"itens": get_financeiro()}


@app.get("/baixas")
def baixas():
    return {"itens": get_all_baixas()}