from fastapi import FastAPI
import requests
import time
import os

app = FastAPI()

# ==============================
# 🔐 CONFIG (Render Environment)
# ==============================
BASE64 = "N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts"
REFRESH_TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.MOcPSvmoMk6dD2mc3O-_xh0DYl_cbZfVyufjuKraKck9dVwyK9-770cxAXDiGQrsNJow7j3PsdGTLjrarPJmhwSWn-aVt07Kl5XaOMTwcl4i5FyUlk_y7FGjQec0VbSxkxRmIyPMtmBMxiM2HgfW47WU7U70mkTWPEgbPdzpCWYyk3S3dytiMGihDp0sqyyXwWctluwNMApfRtiIHneuSlMjlsUobXSrgUrpgWcGWFapS1xaOFryXcvxHeAdaYoyG2_wjVNHsf6jjho_qRvFgJbFSWcrBkXocbOmX7WPP43fVI_Q81XUP13q1uSstlmMNyWRj3BGbET9OVymf7pWTQ.gtg1rOVVZOo78xzZ.S2JxZGNq31r6JqXoI5KktxRW5aUijKJEx3-YANQwvX-b7qagy0wPHHp7uQxRjYxZSKvf-gGHFZVBOxez6qnQx1Llkb2u-10bu5RBGPuG3TMmLDKNLg1N81scp7ofd27dTPyocNg9ape6bhmkoQmw2Z13HQ2NWb6wJ9W7vz8_4KvBysFc6PhHUfYXgFo4lzYN8kF5rCS0mJ9SvGulO-Howz54xnFNiRpVFDYB7cEcizUUJ6p189PWjiDG06A7JJfQavxjcwe6PFsOs7TYlNLdI9mFinjZ4n-5V97Z29hSHmeJ5aWC-V7YyKxTNY0IpF2Pcmy37OZ6TWn73pDw4uXvtqNl3FfSzWGnBXVauJQ2zoFCTO4sO_zxbsrZNLolqWDNJAkMhZ8cT7tEWweo5pzOTdL7o7JHDn3wNniqFHquLnLSwIe0qEsHqX_pMosfoQqTtx5d8-4tqL9vjeRyohos32tLnRx1Nx_Z-LeDco4pG_1DitblevInTXbuS17FpyfSoWhRYtGURtPTbaJfiyjZB4p2-S7x0Azpb2KoHlcOJAg90sk1t8nBjk6vb2eGPEb32hwHB-M6aHuVMbPAx3UEAiZyR1qyETwoM4_7HL79ZvLgVFbKBkpFEQD6UhQtweFwU-pMJEUrle5GezaUriAHPsIYhksyxyQo8snkwAX-FJjdeKiVBNT3YhDE-vlfRxzQi2qvHkGGO2KZo0nSbtmCNqGrE5Iv3Er3jD4caN_SgvPuYXoWheKfUNZJH7MAUsVn-I2knw1fYiPuZ8VLVaP4t1CQWctSWw0nz98LNXIIWFhOHqlcSk8x-j3b2CikRIPsv0DURw4bF6KhozVLIG6-CdF-cGWM3IuRm7q8e0FvPIFX_2cLkIp5L9pg1WOTTPLBlrXZ-fNX6hWulzNxlzf3Ew7x1d7kiilz62z2Xqai29JukrRs0KcI4_5UnFWw-p02fKSAONUZn3SHwWd4wSj1PGBvnpebxn2E4k3HsNrKwyirzVYAObhsL3JQ0LRt0MOCS-a1uxaN2Cr4chJT2u7FNBOQaQ9ntO9DhxgXBTdN_hW29ll0dGTmZmyJ-53zyHVfOD_I91-K-bpkDlTur0fsWH4_nL5hUcW6HMBITUHBnJw1CSNWmxwK0XEsa1jeqzHE0X4c2C2kpvR-UxG4lqgXAxv3xHMQYOqxJ-ISGYpfYWr_LWuckTgYFc5KGVRTR5taTvT9xGWL20wF7TLTqtTFREJZ0LX8fNabnsldC22KUb5X_mFQD7VGY-SfAHFZ0tyYxQ4_xJpqjT7XYb5K5w9PHK-Jmj9c_RYpHf2z7wQcYI4izw.404pc3yCq883fceS_TBelQ"

# ==============================
# 🔄 TOKEN CACHE
# ==============================
ACCESS_TOKEN = None
TOKEN_EXPIRATION = 0


# ==============================
# 🔑 AUTH MANAGER
# ==============================
def get_access_token():
    global ACCESS_TOKEN, TOKEN_EXPIRATION

    if ACCESS_TOKEN and time.time() < TOKEN_EXPIRATION:
        return ACCESS_TOKEN

    url = "https://auth.contaazul.com/oauth2/token"

    headers = {
        "Authorization": f"Basic {BASE64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = f"grant_type=refresh_token&refresh_token={REFRESH_TOKEN}"

    response = requests.post(url, headers=headers, data=payload)

    print("\n==== TOKEN REQUEST ====")
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
    print("======================\n")

    try:
        data = response.json()
    except:
        raise Exception(f"Erro ao converter token: {response.text}")

    if "access_token" not in data:
        return {
            "erro": "refresh_token_expirado",
            "detalhe": data
        }

    ACCESS_TOKEN = data["access_token"]
    TOKEN_EXPIRATION = time.time() + data.get("expires_in", 3600) - 60

    return ACCESS_TOKEN


# ==============================
# 🌐 CLIENT GENÉRICO
# ==============================
def contaazul_get(endpoint, params=None):
    token = get_access_token()

    if isinstance(token, dict):
        return token

    url = f"https://api-v2.contaazul.com{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers, params=params)

    print("\n==== API REQUEST ====")
    print("URL:", url)
    print("STATUS:", response.status_code)
    print("=====================\n")

    try:
        return response.json()
    except:
        return {
            "erro": "resposta_invalida",
            "status": response.status_code,
            "conteudo": response.text
        }


# ==============================
# 📊 ENDPOINTS
# ==============================

@app.get("/")
def home():
    return {"status": "API Conta Azul rodando 🚀"}


# 📊 DRE
@app.get("/dre-categorias")
def dre_categorias():
    return contaazul_get("/v1/financeiro/categorias-dre")


# 📁 Categorias financeiras
@app.get("/categorias")
def categorias():
    return contaazul_get("/v1/categorias")


# 🏢 Centro de custo
@app.get("/centro-custo")
def centro_custo():
    return contaazul_get("/v1/centro-de-custo")


# 🏦 CONTAS FINANCEIRAS (NOVO 🔥)
@app.get("/contas-financeiras")
def contas_financeiras():
    return contaazul_get("/v1/conta-financeira")


# ==============================
# 💰 CONTAS A RECEBER
# ==============================
@app.get("/contas-receber")
def contas_receber():
    pagina = 1
    resultado = []

    while True:
        data = contaazul_get(
            "/v1/financeiro/eventos-financeiros/contas-a-receber",
            params={"pagina": pagina, "tamanho_pagina": 100}
        )

        if "itens" not in data:
            return data

        itens = data["itens"]

        if not itens:
            break

        resultado.extend(itens)
        pagina += 1

    return resultado


# ==============================
# 💸 CONTAS A PAGAR
# ==============================
@app.get("/contas-pagar")
def contas_pagar():
    pagina = 1
    resultado = []

    while True:
        data = contaazul_get(
            "/v1/financeiro/eventos-financeiros/contas-a-pagar",
            params={"pagina": pagina, "tamanho_pagina": 100}
        )

        if "itens" not in data:
            return data

        itens = data["itens"]

        if not itens:
            break

        resultado.extend(itens)
        pagina += 1

    return resultado