from fastapi import FastAPI
import requests
import os
import psycopg2
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI()

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
def get_all(endpoint):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    pagina = 1
    todos = []

    while True:
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params={
                "pagina": pagina,
                "tamanho_pagina": 100,
                "data_vencimento_de": "2023-01-01",
                "data_vencimento_ate": "2035-12-31"
            }
        )

        data = r.json()
        itens = data.get("itens", [])

        if not itens:
            break

        todos.extend(itens)
        pagina += 1

    return todos

# =========================
# BAIXA
# =========================
def get_baixa(id_parcela, headers):
    try:
        r = requests.get(
            f"{BASE_URL}/v1/financeiro/eventos-financeiros/parcelas/{id_parcela}/baixa",
            headers=headers
        )
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# =========================
# ETL PRINCIPAL
# =========================
@app.get("/etl")
def executar_etl():

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    receber = get_all("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")
    pagar = get_all("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")

    todos = []

    for x in receber:
        x["tipo"] = "RECEBER"
        todos.append(x)

    for x in pagar:
        x["tipo"] = "PAGAR"
        todos.append(x)

    # 🔥 buscar baixas
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(get_baixa, item["id"], headers): item
            for item in todos
        }

        for future in as_completed(futures):
            item = futures[future]
            baixa = future.result()

            if baixa:
                item["data_pagamento"] = baixa.get("data_pagamento")
                item["metodo_pagamento"] = baixa.get("metodo_pagamento")

    # =========================
    # SALVAR NO BANCO
    # =========================
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM fato_financeiro")

    for item in todos:
        cur.execute("""
            INSERT INTO fato_financeiro (
                id, tipo, descricao, total,
                data_vencimento, data_competencia,
                data_pagamento, metodo_pagamento,
                cliente, fornecedor, categoria
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            item.get("id"),
            item.get("tipo"),
            item.get("descricao"),
            item.get("total"),
            item.get("data_vencimento"),
            item.get("data_competencia"),
            item.get("data_pagamento"),
            item.get("metodo_pagamento"),
            (item.get("cliente") or {}).get("nome") if item.get("cliente") else None,
            (item.get("fornecedor") or {}).get("nome") if item.get("fornecedor") else None,
            (item.get("categorias")[0]["nome"] if item.get("categorias") else None)
        ))

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "ETL concluído", "linhas": len(todos)}

# =========================
# API PARA POWER BI
# =========================
@app.get("/financeiro")
def financeiro():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM fato_financeiro")
    colnames = [desc[0] for desc in cur.description]

    rows = cur.fetchall()

    cur.close()
    conn.close()

    itens = [dict(zip(colnames, row)) for row in rows]

    return {"itens": itens}