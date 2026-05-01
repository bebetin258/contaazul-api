from fastapi import FastAPI
import requests
import os
import psycopg2

app = FastAPI()

VERSION = "v11.0 - BAIXAS CORRIGIDAS"
print(f"🚀 SUBIU: {VERSION}")

BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64 = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")


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
# TOKEN
# =========================
def get_access_token():
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
        raise Exception(data)

    update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# CACHE DE BAIXAS
# =========================
cache_baixas = {}


def buscar_baixa(parcela_id, token):
    if not parcela_id:
        return None

    if parcela_id in cache_baixas:
        return cache_baixas[parcela_id]

    response = requests.get(
        f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{parcela_id}/baixa",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        return None

    data = response.json()
    cache_baixas[parcela_id] = data

    return data


# =========================
# PAGINAÇÃO
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

    return resultado, token


# =========================
# ENRIQUECER COM BAIXAS
# =========================
def adicionar_baixas(itens, token):
    for item in itens:

        parcela_id = item.get("id")

        baixa = buscar_baixa(parcela_id, token)

        if baixa:
            item["data_pagamento"] = baixa.get("data_pagamento")
            item["metodo_pagamento"] = baixa.get("metodo_pagamento")
        else:
            item["data_pagamento"] = None
            item["metodo_pagamento"] = None

    return itens


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def home():
    return {"status": "ok", "version": VERSION}


@app.get("/contas-pagar")
def contas_pagar():
    dados, token = buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "tamanho_pagina": 100,
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )

    return adicionar_baixas(dados, token)


@app.get("/contas-receber")
def contas_receber():
    dados, token = buscar_todos(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "tamanho_pagina": 100,
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )

    return adicionar_baixas(dados, token)


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