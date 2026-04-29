from fastapi import FastAPI
import requests
import os
import psycopg2

app = FastAPI()

print("🔥 NOVA VERSÃO SUBIU")
# =========================
# CONFIG (CORRIGIDO)
# =========================
BASE_URL = "https://api-v2.contaazul.com"  # 🔥 SEM /api
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
        params = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        if params_extra:
            params.update(params_extra)

        response = requests.get(
            f"{BASE_URL}{endpoint}",  # 🔥 aqui usa /v1/...
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )

        if response.status_code != 200:
            print("Erro API:", response.text)
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
# LIMPEZA
# =========================
def limpar_lista(lista):
    return [
        {k: ("" if v is None else v) for k, v in item.items()}
        for item in lista if isinstance(item, dict)
    ]


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def home():
    return {"status": "API Conta Azul OK 🚀"}


# 🔥 CONTAS PAGAR DETALHADO (CORRIGIDO)
@app.get("/contas-pagar-detalhado")
def contas_pagar_detalhado():
    token = get_access_token()

    pagina = 1
    resultado = []

    while True:
        response = requests.get(
            f"{BASE_URL}/v1/financeiro/contas-a-pagar",  # 🔥 CORRETO
            headers={"Authorization": f"Bearer {token}"},
            params={
                "pagina": pagina,
                "tamanho_pagina": 100,
                "data_vencimento_de": "2000-01-01",
                "data_vencimento_ate": "2100-01-01"
            }
        )

        if response.status_code != 200:
            print("Erro Conta Azul:", response.text)
            break

        data = response.json()
        itens = data.get("itens", [])

        if not itens:
            break

        for conta in itens:

            baixas = conta.get("baixas", [])

            # NÃO PAGO
            if not baixas:
                resultado.append({
                    "id": conta.get("id"),
                    "descricao": conta.get("descricao"),
                    "status": conta.get("status"),
                    "data_vencimento": conta.get("data_vencimento"),
                    "data_pagamento": None,
                    "valor": conta.get("valor_liquido_total"),
                    "valor_pago": 0
                })

            # PAGO
            for baixa in baixas:
                resultado.append({
                    "id": conta.get("id"),
                    "descricao": conta.get("descricao"),
                    "status": conta.get("status"),
                    "data_vencimento": conta.get("data_vencimento"),
                    "data_pagamento": baixa.get("data_baixa"),
                    "valor": conta.get("valor_liquido_total"),
                    "valor_pago": baixa.get("composicao_valor", {}).get("valor_liquido")
                })

        if len(itens) < 100:
            break

        pagina += 1

    return resultado