from fastapi import FastAPI, HTTPException
import requests
import os
import psycopg2

app = FastAPI()

# =========================
# CONFIG
# =========================
BASE_URL = "https://api-v2.contaazul.com"
TOKEN_URL = "https://auth.contaazul.com/oauth2/token"

BASE64 = os.getenv("BASE64_AUTH")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BASE64 or not DATABASE_URL:
    raise Exception("Variáveis de ambiente não configuradas")

# =========================
# BANCO (SUPABASE)
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_refresh_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens WHERE id = 1")
    result = cur.fetchone()

    cur.close()
    conn.close()

    if not result:
        raise Exception("❌ Refresh token não encontrado no banco")

    print("🔑 TOKEN ATUAL:", result[0][:30], "...")

    return result[0]


def update_refresh_token(new_token):
    print("🔄 ATUALIZANDO REFRESH TOKEN...")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tokens
        SET refresh_token = %s
        WHERE id = 1
    """, (new_token,))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ TOKEN ATUALIZADO COM SUCESSO")


# =========================
# TOKEN AUTOMÁTICO (COM DEBUG)
# =========================
def get_access_token():
    try:
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

        print("📡 STATUS TOKEN:", response.status_code)
        print("📡 RESPOSTA TOKEN:", response.text)

        if response.status_code != 200:
            raise Exception(f"❌ ERRO TOKEN: {response.text}")

        data = response.json()

        # Atualiza refresh token SEMPRE
        if "refresh_token" in data:
            update_refresh_token(data["refresh_token"])

        print("✅ ACCESS TOKEN GERADO")

        return data["access_token"]

    except Exception as e:
        print("🔥 ERRO GERAL TOKEN:", str(e))
        raise e


# =========================
# PAGINAÇÃO
# =========================
def get_all_pages(endpoint, extra_params=None):
    access_token = get_access_token()

    pagina = 1
    resultado_final = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        if extra_params:
            params.update(extra_params)

        print(f"📄 Página {pagina}")

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            params=params
        )

        print("📡 STATUS API:", response.status_code)

        if response.status_code != 200:
            print("❌ ERRO API:", response.text)
            raise Exception(f"Erro API: {response.text}")

        data = response.json()

        itens = data.get("itens") or data.get("items") or []

        print(f"📦 Registros na página: {len(itens)}")

        if not itens:
            break

        resultado_final.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    print(f"✅ TOTAL FINAL: {len(resultado_final)}")

    return resultado_final


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def home():
    return {"status": "API rodando 🚀"}


@app.get("/categorias")
def categorias():
    try:
        return get_all_pages("/v1/categorias")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/centro-custo")
def centro_custo():
    try:
        return get_all_pages("/v1/centro-de-custo")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categorias-dre")
def categorias_dre():
    try:
        access_token = get_access_token()

        response = requests.get(
            f"{BASE_URL}/v1/financeiro/categorias-dre",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print("📡 STATUS DRE:", response.status_code)

        if response.status_code != 200:
            raise Exception(response.text)

        data = response.json()

        return data.get("itens") or data.get("items") or data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contas-financeiras")
def contas_financeiras():
    try:
        access_token = get_access_token()

        response = requests.get(
            f"{BASE_URL}/v1/conta-financeira",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print("📡 STATUS FINANCEIRAS:", response.status_code)

        if response.status_code != 200:
            raise Exception(response.text)

        data = response.json()

        return data.get("itens") or data.get("items") or data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contas-receber")
def contas_receber():
    try:
        return get_all_pages(
            "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
            {
                "data_vencimento_de": "1900-01-01",
                "data_vencimento_ate": "2100-12-31"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contas-pagar")
def contas_pagar():
    try:
        return get_all_pages(
            "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
            {
                "data_vencimento_de": "1900-01-01",
                "data_vencimento_ate": "2100-12-31"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))