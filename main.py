from fastapi import FastAPI
import requests
import os
import psycopg2
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI()

# =========================
# CONFIG
# =========================
BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64_AUTH = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")

MAX_WORKERS = 8
TIMEOUT = 10
RETRY = 3

# =========================
# CACHE TOKEN
# =========================
ACCESS_TOKEN_CACHE = {
    "token": None,
    "expires_at": 0
}

# =========================
# DB
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)

# =========================
# TOKEN SEGURO
# =========================
def get_access_token():
    now = time.time()

    if ACCESS_TOKEN_CACHE["token"] and now < ACCESS_TOKEN_CACHE["expires_at"]:
        return ACCESS_TOKEN_CACHE["token"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens LIMIT 1 FOR UPDATE")
    refresh_token = cur.fetchone()[0]

    try:
        response = requests.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {BASE64_AUTH}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            conn.rollback()
            raise Exception("Erro ao renovar token")

        data = response.json()

        cur.execute(
            "UPDATE tokens SET refresh_token = %s",
            (data["refresh_token"],)
        )

        conn.commit()

        ACCESS_TOKEN_CACHE["token"] = data["access_token"]
        ACCESS_TOKEN_CACHE["expires_at"] = now + 3500

        return data["access_token"]

    finally:
        cur.close()
        conn.close()

# =========================
# PAGINAÇÃO SEGURA
# =========================
def get_all_pages(endpoint, params_extra=None):
    token = get_access_token()

    headers = {"Authorization": f"Bearer {token}"}

    pagina = 1
    tamanho_pagina = 100
    todos = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": tamanho_pagina,
            **(params_extra or {})
        }

        try:
            r = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                params=params,
                timeout=TIMEOUT
            )

            if r.status_code != 200:
                break

            data = r.json()
            itens = data.get("itens", [])

            if not itens:
                break

            todos.extend(itens)

            if len(itens) < tamanho_pagina:
                break

            pagina += 1

        except:
            break

    return todos

# =========================
# PADRONIZAÇÃO (CRÍTICO)
# =========================
def padronizar_item(item):
    return {
        "id": item.get("id"),
        "status": item.get("status"),
        "total": item.get("total"),
        "descricao": item.get("descricao"),
        "data_vencimento": item.get("data_vencimento"),
        "data_competencia": item.get("data_competencia"),
        "data_criacao": item.get("data_criacao"),
        "data_alteracao": item.get("data_alteracao"),
        "categorias": item.get("categorias", []),
        "centros_de_custo": item.get("centros_de_custo", []),
        "cliente": item.get("cliente"),
        "fornecedor": item.get("fornecedor"),
        "data_pagamento": None,
        "metodo_pagamento": None
    }

# =========================
# BAIXA COM RETRY
# =========================
def buscar_baixa(id_parcela, headers):
    for _ in range(RETRY):
        try:
            r = requests.get(
                f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{id_parcela}/baixa",
                headers=headers,
                timeout=TIMEOUT
            )

            if r.status_code != 200:
                continue

            data = r.json()

            if isinstance(data, list):
                return data[0] if data else None

            return data

        except:
            time.sleep(1)

    return None

# =========================
# ENDPOINT FINAL
# =========================
@app.get("/financeiro-completo")
def financeiro_completo():

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    receber = get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )

    pagar = get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "data_vencimento_de": "2023-01-01",
            "data_vencimento_ate": "2035-12-31"
        }
    )

    todos = [padronizar_item(x) for x in (receber + pagar)]

    # 🔥 THREAD POOL CONTROLADO
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(buscar_baixa, item["id"], headers): item
            for item in todos
        }

        for future in as_completed(futures):
            item = futures[future]
            baixa = future.result()

            if baixa:
                item["data_pagamento"] = baixa.get("data_pagamento")
                item["metodo_pagamento"] = baixa.get("metodo_pagamento")

    return {"itens": todos}


@app.get("/")
def home():
    return {"status": "API ENTERPRISE OK"}