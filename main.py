from fastapi import FastAPI
import requests
import psycopg2
import os
import time
from datetime import datetime

app = FastAPI()

# ==============================
# CONFIG
# ==============================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

BASE_URL = "https://api-v2.contaazul.com"

# ==============================
# TOKEN SEGURO (NÃO QUEBRA APP)
# ==============================
def get_access_token():
    try:
        url = "https://api.contaazul.com/oauth2/token"

        response = requests.post(
            url,
            auth=(CLIENT_ID, CLIENT_SECRET),
            data={
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN
            },
            timeout=10
        )

        if response.status_code != 200:
            print("❌ ERRO TOKEN:", response.text)
            return None

        return response.json().get("access_token")

    except Exception as e:
        print("❌ ERRO TOKEN:", e)
        return None


# ==============================
# DB
# ==============================
def get_conn():
    return psycopg2.connect(DB_URL)


# ==============================
# PAGINAÇÃO SEGURA
# ==============================
def fetch_all(endpoint):
    token = get_access_token()

    if not token:
        print("⚠️ Sem token, abortando fetch")
        return []

    headers = {"Authorization": f"Bearer {token}"}

    pagina = 1
    all_data = []

    while True:
        print(f"📄 Página {pagina}")

        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                params={
                    "pagina": pagina,
                    "tamanho_pagina": 100
                },
                timeout=15
            )

            if response.status_code == 401:
                print("🔄 Token expirou")
                return all_data

            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict):
                itens = data.get("itens", [])
            else:
                itens = data

            if not itens:
                break

            all_data.extend(itens)

            if len(itens) < 100:
                break

            pagina += 1
            time.sleep(0.2)

        except Exception as e:
            print("❌ ERRO FETCH:", e)
            break

    return all_data


# ==============================
# TRANSFORMAÇÃO CORRETA
# ==============================
def tratar_item(item, tipo):
    return {
        "id": item.get("id"),
        "tipo": tipo,
        "descricao": item.get("descricao"),

        "total": item.get("valor", {}).get("total"),

        "data_vencimento": item.get("parcela", {}).get("data_vencimento"),
        "data_competencia": item.get("data_competencia"),

        "data_pagamento": item.get("data_pagamento"),
        "metodo_pagamento": item.get("metodo_pagamento"),

        "cliente": (
            item.get("cliente", {}).get("nome")
            if isinstance(item.get("cliente"), dict)
            else None
        ),

        "fornecedor": (
            item.get("fornecedor", {}).get("nome")
            if isinstance(item.get("fornecedor"), dict)
            else None
        ),

        "categoria": (
            item.get("categorias")[0]["nome"]
            if item.get("categorias") and isinstance(item.get("categorias"), list)
            else None
        ),

        "atualizado_em": datetime.now()
    }


# ==============================
# ETL (AGORA NÃO QUEBRA MAIS)
# ==============================
def run_etl():
    print("🚀 ETL INICIADO")

    receber = fetch_all("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")
    pagar = fetch_all("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")

    print("📥 RECEBER:", len(receber))
    print("📤 PAGAR:", len(pagar))

    if not receber and not pagar:
        print("⚠️ Nenhum dado - abortando ETL")
        return

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM fato_financeiro")

    for item in receber:
        inserir(cur, tratar_item(item, "RECEBER"))

    for item in pagar:
        inserir(cur, tratar_item(item, "PAGAR"))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ ETL FINALIZADO")


def inserir(cur, item):
    cur.execute("""
        INSERT INTO fato_financeiro (
            id, tipo, descricao, total,
            data_vencimento, data_competencia,
            data_pagamento, metodo_pagamento,
            cliente, fornecedor, categoria, atualizado_em
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (
        item["id"],
        item["tipo"],
        item["descricao"],
        item["total"],
        item["data_vencimento"],
        item["data_competencia"],
        item["data_pagamento"],
        item["metodo_pagamento"],
        item["cliente"],
        item["fornecedor"],
        item["categoria"],
        item["atualizado_em"]
    ))


# ==============================
# 🚫 REMOVIDO STARTUP AUTOMÁTICO
# ==============================
# NÃO rodar ETL aqui


# ==============================
# ENDPOINTS
# ==============================
@app.get("/financeiro")
def financeiro():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM fato_financeiro")
    rows = cur.fetchall()

    cols = [desc[0] for desc in cur.description]
    result = [dict(zip(cols, row)) for row in rows]

    cur.close()
    conn.close()

    return {"itens": result}


@app.get("/etl")
def etl():
    run_etl()
    return {"status": "ETL executado"}


@app.get("/status")
def status():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fato_financeiro")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {"linhas": total}