from fastapi import FastAPI
import requests
import os
import psycopg2
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64_AUTH = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")

INTERVALO_ETL = 1800  # 30 minutos

# =========================
# DB
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)

# =========================
# TOKEN
# =========================
def get_access_token():
    print("🔑 Gerando access token...")

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

    print("✅ Token atualizado")

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
        print(f"📄 Página {pagina} - {endpoint}")

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

        if r.status_code != 200:
            print("❌ Erro na API:", r.text)
            break

        data = r.json()
        itens = data.get("itens", [])

        if not itens:
            break

        todos.extend(itens)
        pagina += 1

    return todos

# =========================
# BAIXAS
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
# ETL
# =========================
def executar_etl():
    print("\n🚀 INICIANDO ETL\n")

    try:
        token = get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        receber = get_all("/v1/financeiro/eventos-financeiros/contas-a-receber/buscar")
        print(f"📥 RECEBER: {len(receber)}")

        pagar = get_all("/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar")
        print(f"📤 PAGAR: {len(pagar)}")

        todos = []

        for x in receber:
            x["tipo"] = "RECEBER"
            todos.append(x)

        for x in pagar:
            x["tipo"] = "PAGAR"
            todos.append(x)

        print(f"📊 TOTAL: {len(todos)}")

        # BAIXAS
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(get_baixa, item["id"], headers): item
                for item in todos
            }

            for future in as_completed(futures):
                item = futures[future]
                baixa = future.result()

if isinstance(baixa, dict):
    item["data_pagamento"] = baixa.get("data_pagamento")
else:
    item["data_pagamento"] = None

        # SALVAR
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM fato_financeiro")

        for item in todos:
            cur.execute("""
                INSERT INTO fato_financeiro (id, tipo, descricao, data_pagamento)
                VALUES (%s,%s,%s,%s)
            """, (
                item.get("id"),
                item.get("tipo"),
                item.get("descricao"),
                item.get("data_pagamento")
            ))

        conn.commit()
        cur.close()
        conn.close()

        print(f"\n✅ ETL FINALIZADO: {len(todos)} registros\n")

    except Exception as e:
        print("\n❌ ERRO NO ETL:", str(e), "\n")

# =========================
# LOOP AUTOMÁTICO
# =========================
def loop_etl():
    while True:
        executar_etl()
        time.sleep(INTERVALO_ETL)

@app.on_event("startup")
def start_etl():
    print("🔥 STARTUP: executando ETL inicial")

    executar_etl()

    thread = threading.Thread(target=loop_etl, daemon=True)
    thread.start()

# =========================
# ENDPOINTS
# =========================

@app.get("/etl")
def rodar_etl_manual():
    executar_etl()
    return {"status": "ETL executado"}

@app.get("/status")
def status():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fato_financeiro")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {"linhas": total}

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

# =========================
# ENDPOINTS AUXILIARES
# =========================

@app.get("/categorias")
def categorias():
    token = get_access_token()
    r = requests.get(
        f"{BASE_URL}/v1/categorias",
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.json()

@app.get("/categorias-dre")
def categorias_dre():
    token = get_access_token()
    r = requests.get(
        f"{BASE_URL}/v1/financeiro/categorias-dre",
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.json()

@app.get("/conta-financeira")
def conta_financeira():
    token = get_access_token()
    r = requests.get(
        f"{BASE_URL}/v1/conta-financeira",
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.json()

# =========================
# HEALTHCHECK
# =========================
@app.get("/")
def home():
    return {"status": "API rodando com ETL automático"}