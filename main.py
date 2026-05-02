from fastapi import FastAPI
import requests
import psycopg2
import os
import time
from datetime import datetime

app = FastAPI()

# ==============================
# 🔐 CONFIG
# ==============================
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

DB_URL = os.getenv("DATABASE_URL")

BASE_URL = "https://api-v2.contaazul.com"

# ==============================
# 🔐 TOKEN AUTOMÁTICO
# ==============================
def get_access_token():
    url = "https://api.contaazul.com/oauth2/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }

    response = requests.post(url, auth=(CLIENT_ID, CLIENT_SECRET), data=payload)
    response.raise_for_status()

    return response.json()["access_token"]

# ==============================
# 📦 CONEXÃO DB
# ==============================
def get_conn():
    return psycopg2.connect(DB_URL)

# ==============================
# 🔄 PAGINAÇÃO
# ==============================
def fetch_all(endpoint):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    pagina = 1
    all_data = []

    while True:
        print(f"📄 Página {pagina} - {endpoint}")

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params={
                "pagina": pagina,
                "tamanho_pagina": 100
            }
        )

        if response.status_code == 401:
            print("🔄 Token expirado, renovando...")
            token = get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            continue

        response.raise_for_status()

        data = response.json()

        # 🔥 TRATAMENTO UNIVERSAL
        if isinstance(data, dict):
            itens = data.get("itens", [])
        elif isinstance(data, list):
            itens = data
        else:
            itens = []

        if not itens:
            break

        all_data.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1
        time.sleep(0.3)

    return all_data

# ==============================
# 🧠 TRANSFORMAÇÃO (ESSENCIAL)
# ==============================
def tratar_item(item, tipo):

    return {
        "id": item.get("id"),
        "tipo": tipo,
        "descricao": item.get("descricao"),

        "total": item.get("valor", {}).get("total"),

        "data_vencimento": (
            item.get("parcela", {}).get("data_vencimento")
        ),

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
# 🏗️ ETL PRINCIPAL
# ==============================
def run_etl():
    print("🚀 INICIANDO ETL")

    conn = get_conn()
    cur = conn.cursor()

    # recria tabela (modo simples e confiável)
    cur.execute("DROP TABLE IF EXISTS fato_financeiro")

    cur.execute("""
    CREATE TABLE fato_financeiro (
        id TEXT PRIMARY KEY,
        tipo TEXT,
        descricao TEXT,
        total NUMERIC,
        data_vencimento DATE,
        data_competencia DATE,
        data_pagamento DATE,
        metodo_pagamento TEXT,
        cliente TEXT,
        fornecedor TEXT,
        categoria TEXT,
        atualizado_em TIMESTAMP
    )
    """)

    conn.commit()

    # ==============================
    # 📥 CONTAS A RECEBER
    # ==============================
    receber = fetch_all("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")
    print(f"📥 RECEBER: {len(receber)}")

    # ==============================
    # 📤 CONTAS A PAGAR
    # ==============================
    pagar = fetch_all("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")
    print(f"📤 PAGAR: {len(pagar)}")

    total = receber + pagar
    print(f"📊 TOTAL: {len(total)}")

    # ==============================
    # 💾 INSERT
    # ==============================
    for item in total:
        tipo = "RECEBER" if item in receber else "PAGAR"

        item_tratado = tratar_item(item, tipo)

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
            item_tratado["id"],
            item_tratado["tipo"],
            item_tratado["descricao"],
            item_tratado["total"],
            item_tratado["data_vencimento"],
            item_tratado["data_competencia"],
            item_tratado["data_pagamento"],
            item_tratado["metodo_pagamento"],
            item_tratado["cliente"],
            item_tratado["fornecedor"],
            item_tratado["categoria"],
            item_tratado["atualizado_em"]
        ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ ETL FINALIZADO")

# ==============================
# 🔥 AUTO START (IMPORTANTE)
# ==============================
@app.on_event("startup")
def startup():
    run_etl()

# ==============================
# 🌐 ENDPOINTS
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

@app.get("/status")
def status():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fato_financeiro")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {"linhas": total}

@app.get("/etl")
def etl():
    run_etl()
    return {"status": "ETL executado"}