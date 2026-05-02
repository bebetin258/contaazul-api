from fastapi import FastAPI
import requests
import os
import psycopg2
import json
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

# =========================
# DB
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)

# =========================
# TOKEN
# =========================
def get_access_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens LIMIT 1")
    refresh_token = cur.fetchone()[0]

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {BASE64_AUTH}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )

    data = response.json()

    cur.execute(
        "UPDATE tokens SET refresh_token = %s",
        (data["refresh_token"],)
    )

    conn.commit()
    cur.close()
    conn.close()

    return data["access_token"]

# =========================
# PAGINAÇÃO
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

        r = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=params
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

    return todos

# =========================
# BAIXA
# =========================
def buscar_baixa(id_parcela, headers):
    try:
        r = requests.get(
            f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{id_parcela}/baixa",
            headers=headers
        )

        if r.status_code != 200:
            return None

        data = r.json()

        if isinstance(data, list):
            return data[0] if data else None

        return data

    except:
        return None

# =========================
# SALVAR CACHE
# =========================
def salvar_cache(itens):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM financeiro_cache")

    for item in itens:
        cur.execute(
            "INSERT INTO financeiro_cache (id, data) VALUES (%s, %s)",
            (item["id"], json.dumps(item))
        )

    conn.commit()
    cur.close()
    conn.close()

# =========================
# PROCESSAMENTO PESADO
# =========================
@app.get("/atualizar-cache")
def atualizar_cache():

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

    todos = receber + pagar

    # 🔥 BUSCA BAIXAS
    with ThreadPoolExecutor(max_workers=6) as executor:
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
            else:
                item["data_pagamento"] = None
                item["metodo_pagamento"] = None

    salvar_cache(todos)

    return {"status": "cache atualizado", "total": len(todos)}

# =========================
# ENDPOINT LEVE (POWER BI)
# =========================
@app.get("/financeiro")
def financeiro():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT data FROM financeiro_cache")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    itens = [r[0] for r in rows]

    return {"itens": itens}

# =========================
# HEALTHCHECK
# =========================
@app.get("/")
def home():
    return {"status": "OK"}