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
        raise Exception(f"Erro ao renovar token: {response.text}")

    data = response.json()

    # 🔥 Atualiza SEMPRE o refresh_token
    update_refresh_token(data["refresh_token"])

    return data["access_token"]


# =========================
# PAGINAÇÃO PADRÃO
# =========================
def get_all_pages(endpoint, params_extra=None):
    token = get_access_token()

    pagina = 1
    resultado = []

    while True:
        params = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        if params_extra:
            params.update(params_extra)

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )

        if response.status_code != 200:
            print("Erro API:", response.text)
            break

        data = response.json()

        itens = data.get("items") or data.get("itens") or []

        if not isinstance(itens, list) or len(itens) == 0:
            break

        resultado.extend(itens)

        if len(itens) < 100:
            break

        pagina += 1

    return resultado


# =========================
# FLATTEN DRE (POWER BI SAFE)
# =========================
def flatten_dre(data):
    resultado = []

    def percorrer(item, nivel_1=None, nivel_2=None):
        try:
            desc = item.get("descricao", "")

            if not nivel_1:
                nivel_1 = desc
            elif not nivel_2:
                nivel_2 = desc

            categorias = item.get("categorias_financeiras") or []

            if isinstance(categorias, list) and categorias:
                for cat in categorias:
                    if isinstance(cat, dict):
                        resultado.append({
                            "nivel_1": str(nivel_1 or ""),
                            "nivel_2": str(nivel_2 or ""),
                            "categoria_financeira": str(cat.get("nome") or ""),
                            "codigo_categoria": str(cat.get("codigo") or ""),
                            "ativo": bool(cat.get("ativo", False))
                        })
            else:
                resultado.append({
                    "nivel_1": str(nivel_1 or ""),
                    "nivel_2": str(nivel_2 or ""),
                    "categoria_financeira": "",
                    "codigo_categoria": "",
                    "ativo": False
                })

            subitens = item.get("subitens") or []

            if isinstance(subitens, list):
                for sub in subitens:
                    if isinstance(sub, dict):
                        percorrer(sub, nivel_1, nivel_2)

        except Exception as e:
            print("Erro flatten:", e)

    for item in data:
        if isinstance(item, dict):
            percorrer(item)

    return resultado


# =========================
# ENDPOINTS
# =========================
@app.get("/")
def home():
    return {"status": "API Conta Azul rodando 🚀"}


@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")


@app.get("/centro-custo")
def centro_custo():
    return get_all_pages("/v1/centro-de-custo")


@app.get("/contas-financeiras")
def contas_financeiras():
    return get_all_pages("/v1/conta-financeira")


@app.get("/categorias-dre")
def categorias_dre():
    try:
        token = get_access_token()

        response = requests.get(
            f"{BASE_URL}/v1/financeiro/categorias-dre",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code != 200:
            print(response.text)
            return []

        data = response.json()

        # 🔥 GARANTE LISTA
        if isinstance(data, dict):
            data = data.get("itens", [])

        if not isinstance(data, list):
            return []

        resultado = flatten_dre(data)

        # 🔥 BLINDAGEM FINAL (POWER BI SAFE)
        resultado_limpo = []

        for item in resultado:
            if isinstance(item, dict):
                resultado_limpo.append({
                    "nivel_1": str(item.get("nivel_1", "")),
                    "nivel_2": str(item.get("nivel_2", "")),
                    "categoria_financeira": str(item.get("categoria_financeira", "")),
                    "codigo_categoria": str(item.get("codigo_categoria", "")),
                    "ativo": bool(item.get("ativo", False))
                })

        return resultado_limpo

    except Exception as e:
        print("Erro categorias-dre:", str(e))
        return []


@app.get("/contas-receber")
def contas_receber():
    return get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-receber/buscar",
        {
            "data_vencimento_de": "2000-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )


@app.get("/contas-pagar")
def contas_pagar():
    return get_all_pages(
        "/v1/financeiro/eventos-financeiros/contas-a-pagar/buscar",
        {
            "data_vencimento_de": "2000-01-01",
            "data_vencimento_ate": "2100-01-01"
        }
    )