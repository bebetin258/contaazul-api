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
# CONEXÃO BANCO (SUPABASE)
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
        raise Exception("Refresh token não encontrado no banco")

    return result[0]


def update_refresh_token(new_token):
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


# =========================
# TOKEN AUTOMÁTICO
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

    if response.status_code != 200:
        raise Exception(f"Erro ao renovar token: {response.text}")

    data = response.json()

    # 🔥 Sempre atualizar o refresh_token
    if "refresh_token" in data:
        update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# PAGINAÇÃO GENÉRICA
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

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            params=params
        )

        if response.status_code != 200:
            raise Exception(f"Erro API: {response.text}")

        data = response.json()

        itens = data.get("itens") or data.get("items") or []

        if not itens:
            break

        resultado_final.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    return resultado_final


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def home():
    return {"status": "API Conta Azul rodando 🚀"}


# 📊 CATEGORIAS
@app.get("/categorias")
def categorias():
    try:
        return get_all_pages("/v1/categorias")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 📊 CENTRO DE CUSTO
@app.get("/centro-custo")
def centro_custo():
    try:
        return get_all_pages("/v1/centro-de-custo")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 📊 CATEGORIAS DRE
@app.get("/categorias-dre")
def categorias_dre():
    try:
        access_token = get_access_token()

        response = requests.get(
            f"{BASE_URL}/v1/financeiro/categorias-dre",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 📊 CONTAS FINANCEIRAS
@app.get("/contas-financeiras")
def contas_financeiras():
    try:
        access_token = get_access_token()

        response = requests.get(
            f"{BASE_URL}/v1/conta-financeira",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 💰 CONTAS A RECEBER (TODAS AS DATAS)
@app.get("/contas-receber")
def contas_receber():
    try:
        return get_all_pages(
            "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
            {
                "data_vencimento_de": "2026-01-01",
                "data_vencimento_ate": "2026-12-31"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 💸 CONTAS A PAGAR (TODAS AS DATAS)
@app.get("/contas-pagar")
def contas_pagar():
    try:
        return get_all_pages(
            "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
            {
                "data_vencimento_de": "2026-01-01",
                "data_vencimento_ate": "2026-12-31"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))