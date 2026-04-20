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
# BANCO
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
    cur.execute("UPDATE tokens SET refresh_token = %s WHERE id = 1", (new_token,))
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

    if response.status_code != 200:
        raise Exception(response.text)

    data = response.json()
    update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# PAGINAÇÃO
# =========================
def get_all_pages(endpoint, params_extra=None):
    token = get_access_token()

    pagina = 1
    resultado = []

    while True:
        params = {"pagina": pagina, "tamanho_pagina": 100}

        if params_extra:
            params.update(params_extra)

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )

        if response.status_code != 200:
            print(response.text)
            break

        data = response.json()
        itens = data.get("items") or data.get("itens") or []

        if not itens:
            break

        resultado.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    return resultado


# =========================
# LIMPEZA UNIVERSAL
# =========================
def limpar_dict(d):
    if not isinstance(d, dict):
        return None

    return {k: ("" if v is None else v) for k, v in d.items()}


def limpar_lista(lista):
    resultado = []
    for item in lista:
        limpo = limpar_dict(item)
        if limpo:
            resultado.append(limpo)
    return resultado


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def home():
    return {"status": "API OK 🚀"}


@app.get("/categorias")
def categorias():
    dados = get_all_pages("/v1/categorias")

    resultado = []
    for item in dados:
        if isinstance(item, dict):
            resultado.append({
                "id": str(item.get("id", "")),
                "versao": int(item.get("versao", 0)) if item.get("versao") else 0,
                "nome": str(item.get("nome", "")),
                "categoria_pai": str(item.get("categoria_pai", "")),
                "tipo": str(item.get("tipo", "")),
                "entrada_dre": str(item.get("entrada_dre", "")),
                "considera_custo_dre": bool(item.get("considera_custo_dre", False))
            })

    return resultado


# =========================
# 🔥 CONTAS A RECEBER (CORRIGIDO)
# =========================
@app.get("/contas-receber")
def contas_receber():
    dados = get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "data_vencimento_de": "2000-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )

    return limpar_lista(dados)


# =========================
# 🔥 CONTAS A PAGAR (CORRIGIDO)
# =========================
@app.get("/contas-pagar")
def contas_pagar():
    dados = get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "data_vencimento_de": "2000-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )

    return limpar_lista(dados)


# =========================
# OUTROS
# =========================
@app.get("/centro-custo")
def centro_custo():
    return {"itens": limpar_lista(get_all_pages("/v1/centro-de-custo"))}


@app.get("/contas-financeiras")
def contas_financeiras():
    return {"itens": limpar_lista(get_all_pages("/v1/conta-financeira"))}


@app.get("/categorias-dre")
def categorias_dre():
    token = get_access_token()

    response = requests.get(
        f"{BASE_URL}/v1/financeiro/categorias-dre",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        return {"itens": []}

    data = response.json()

    if isinstance(data, dict):
        itens = data.get("itens", [])
    else:
        itens = data

    return {"itens": limpar_lista(itens)}