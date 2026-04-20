from fastapi import FastAPI
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


# =========================
# CONEXÃO BANCO
# =========================
def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_refresh_token():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT refresh_token FROM tokens WHERE id = 1")
    token = cur.fetchone()

    cur.close()
    conn.close()

    return token[0] if token else None


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

    if not refresh_token:
        raise Exception("Refresh token não encontrado")

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
        print("❌ ERRO TOKEN:", response.text)
        raise Exception("Erro ao renovar token")

    data = response.json()

    # 🔥 sempre atualiza o refresh_token
    update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# PAGINAÇÃO PADRÃO
# =========================
def get_all_pages(endpoint, params_extra=None):
    access_token = get_access_token()

    pagina = 1
    resultado_final = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        if params_extra:
            params.update(params_extra)

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params
        )

        if response.status_code != 200:
            print(f"❌ ERRO API ({endpoint}):", response.text)
            break

        data = response.json()

        # 🔥 TRATAMENTO UNIVERSAL
        if isinstance(data, dict):
            itens = data.get("items") or data.get("itens") or []
        elif isinstance(data, list):
            itens = data
        else:
            print("⚠️ formato inesperado:", data)
            break

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
    return {"status": "API rodando 🚀"}


@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")


@app.get("/centro-custo")
def centro_custo():
    return get_all_pages("/v1/centro-de-custo")


@app.get("/contas-financeiras")
def contas_financeiras():
    return get_all_pages("/v1/conta-financeira")


# 🔥 DRE CORRIGIDO (SEU PROBLEMA PRINCIPAL)
@app.get("/categorias-dre")
def categorias_dre():
    access_token = get_access_token()

    response = requests.get(
        f"{BASE_URL}/v1/financeiro/categorias-dre",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code != 200:
        print("❌ ERRO DRE:", response.text)
        return []

    data = response.json()

    # 🔥 GARANTE LISTA
    if isinstance(data, dict):
        return data.get("itens", [])

    if isinstance(data, list):
        return data

    print("⚠️ formato inesperado:", data)
    return []


@app.get("/contas-receber")
def contas_receber():
    return get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "data_vencimento_de": "2000-01-01",
            "data_vencimento_ate": "2100-12-31"
        }
    )


@app.get("/contas-pagar")
def contas_pagar():
    return get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "data_vencimento_de": "2000-01-01",
            "data_vencimento_ate": "2100-12-31"
        }
    )