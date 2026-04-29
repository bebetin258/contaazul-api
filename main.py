from fastapi import FastAPI
import requests
import os
import psycopg2
from datetime import datetime

app = FastAPI()

# 🔥 IDENTIFICAÇÃO DA VERSÃO (MUDE SEMPRE)
VERSION = "v2.0 - FIX FINAL API CONTA AZUL"
print(f"🚀 SUBIU NOVA VERSÃO: {VERSION}")

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

    if not token:
        raise Exception("❌ Refresh token não encontrado")

    return token[0]


def update_refresh_token(new_token):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE tokens SET refresh_token = %s WHERE id = 1",
        (new_token,)
    )

    conn.commit()
    cur.close()
    conn.close()

    print("🔄 Refresh token atualizado no banco")


# =========================
# TOKEN
# =========================
def get_access_token():
    print("🔐 Buscando access token...")

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

    data = response.json()

    if response.status_code != 200:
        print("❌ ERRO TOKEN:", data)
        raise Exception(data)

    update_refresh_token(data["refresh_token"])

    print("✅ Token renovado com sucesso")

    return data["access_token"]


# =========================
# ENDPOINTS
# =========================

@app.get("/")
def home():
    return {
        "status": "API OK",
        "version": VERSION
    }


@app.get("/contas-pagar-detalhado")
def contas_pagar_detalhado():

    print("📊 Endpoint contas-pagar chamado")

    token = get_access_token()

    pagina = 1
    resultado = []

    while True:
        print(f"➡️ Página {pagina}")

        response = requests.get(
            f"{BASE_URL}/v1/financeiro/contas-a-pagar",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "pagina": pagina,
                "tamanho_pagina": 100,
                "data_vencimento_de": "2000-01-01",
                "data_vencimento_ate": "2100-01-01"
            }
        )

        if response.status_code != 200:
            print("❌ ERRO CONTA AZUL:", response.text)
            break

        data = response.json()
        itens = data.get("itens", [])

        if not itens:
            break

        for conta in itens:
            baixas = conta.get("baixas", [])

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

    print(f"✅ Total registros: {len(resultado)}")

    return resultado