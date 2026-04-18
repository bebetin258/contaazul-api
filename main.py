import os
import requests
from fastapi import FastAPI

app = FastAPI()

# =========================
# 🔐 CONFIGURAÇÕES
# =========================

BASE_URL = "https://api-v2.contaazul.com"

BASE64 = "N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts"
REFRESH_TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.MOcPSvmoMk6dD2mc3O-_xh0DYl_cbZfVyufjuKraKck9dVwyK9-770cxAXDiGQrsNJow7j3PsdGTLjrarPJmhwSWn-aVt07Kl5XaOMTwcl4i5FyUlk_y7FGjQec0VbSxkxRmIyPMtmBMxiM2HgfW47WU7U70mkTWPEgbPdzpCWYyk3S3dytiMGihDp0sqyyXwWctluwNMApfRtiIHneuSlMjlsUobXSrgUrpgWcGWFapS1xaOFryXcvxHeAdaYoyG2_wjVNHsf6jjho_qRvFgJbFSWcrBkXocbOmX7WPP43fVI_Q81XUP13q1uSstlmMNyWRj3BGbET9OVymf7pWTQ.gtg1rOVVZOo78xzZ.S2JxZGNq31r6JqXoI5KktxRW5aUijKJEx3-YANQwvX-b7qagy0wPHHp7uQxRjYxZSKvf-gGHFZVBOxez6qnQx1Llkb2u-10bu5RBGPuG3TMmLDKNLg1N81scp7ofd27dTPyocNg9ape6bhmkoQmw2Z13HQ2NWb6wJ9W7vz8_4KvBysFc6PhHUfYXgFo4lzYN8kF5rCS0mJ9SvGulO-Howz54xnFNiRpVFDYB7cEcizUUJ6p189PWjiDG06A7JJfQavxjcwe6PFsOs7TYlNLdI9mFinjZ4n-5V97Z29hSHmeJ5aWC-V7YyKxTNY0IpF2Pcmy37OZ6TWn73pDw4uXvtqNl3FfSzWGnBXVauJQ2zoFCTO4sO_zxbsrZNLolqWDNJAkMhZ8cT7tEWweo5pzOTdL7o7JHDn3wNniqFHquLnLSwIe0qEsHqX_pMosfoQqTtx5d8-4tqL9vjeRyohos32tLnRx1Nx_Z-LeDco4pG_1DitblevInTXbuS17FpyfSoWhRYtGURtPTbaJfiyjZB4p2-S7x0Azpb2KoHlcOJAg90sk1t8nBjk6vb2eGPEb32hwHB-M6aHuVMbPAx3UEAiZyR1qyETwoM4_7HL79ZvLgVFbKBkpFEQD6UhQtweFwU-pMJEUrle5GezaUriAHPsIYhksyxyQo8snkwAX-FJjdeKiVBNT3YhDE-vlfRxzQi2qvHkGGO2KZo0nSbtmCNqGrE5Iv3Er3jD4caN_SgvPuYXoWheKfUNZJH7MAUsVn-I2knw1fYiPuZ8VLVaP4t1CQWctSWw0nz98LNXIIWFhOHqlcSk8x-j3b2CikRIPsv0DURw4bF6KhozVLIG6-CdF-cGWM3IuRm7q8e0FvPIFX_2cLkIp5L9pg1WOTTPLBlrXZ-fNX6hWulzNxlzf3Ew7x1d7kiilz62z2Xqai29JukrRs0KcI4_5UnFWw-p02fKSAONUZn3SHwWd4wSj1PGBvnpebxn2E4k3HsNrKwyirzVYAObhsL3JQ0LRt0MOCS-a1uxaN2Cr4chJT2u7FNBOQaQ9ntO9DhxgXBTdN_hW29ll0dGTmZmyJ-53zyHVfOD_I91-K-bpkDlTur0fsWH4_nL5hUcW6HMBITUHBnJw1CSNWmxwK0XEsa1jeqzHE0X4c2C2kpvR-UxG4lqgXAxv3xHMQYOqxJ-ISGYpfYWr_LWuckTgYFc5KGVRTR5taTvT9xGWL20wF7TLTqtTFREJZ0LX8fNabnsldC22KUb5X_mFQD7VGY-SfAHFZ0tyYxQ4_xJpqjT7XYb5K5w9PHK-Jmj9c_RYpHf2z7wQcYI4izw.404pc3yCq883fceS_TBelQ"

ACCESS_TOKEN = None


# =========================
# 🔄 GERAR ACCESS TOKEN
# =========================

def get_access_token():
    global ACCESS_TOKEN

    url = "https://auth.contaazul.com/oauth2/token"

    headers = {
        "Authorization": f"Basic {BASE64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        return {
            "erro": "erro_ao_gerar_token",
            "status": response.status_code,
            "detalhe": response.text
        }

    json_data = response.json()

    if "access_token" not in json_data:
        return {
            "erro": "access_token_nao_encontrado",
            "resposta": json_data
        }

    ACCESS_TOKEN = json_data["access_token"]
    return ACCESS_TOKEN


# =========================
# 🔗 CHAMADA API CONTA AZUL
# =========================

def contaazul_get(endpoint, params=None):
    global ACCESS_TOKEN

    if ACCESS_TOKEN is None:
        ACCESS_TOKEN = get_access_token()

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=headers,
        params=params
    )

    # 🔄 se token expirou
    if response.status_code == 401:
        ACCESS_TOKEN = get_access_token()

        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=params
        )

    return response.json()


# =========================
# 📄 PAGINAÇÃO AUTOMÁTICA
# =========================

def get_all_pages(endpoint, params=None):
    pagina = 1
    resultado = []

    while True:
        query = {
            "pagina": pagina,
            "tamanho_pagina": 100
        }

        if params:
            query.update(params)

        data = contaazul_get(endpoint, query)

        if "itens" not in data:
            return data

        itens = data["itens"]

        if not itens:
            break

        resultado.extend(itens)
        pagina += 1

    return resultado


# =========================
# 📊 ENDPOINTS PARA POWER BI
# =========================

@app.get("/")
def home():
    return {"status": "API Conta Azul rodando 🚀"}


@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")


@app.get("/contas-financeiras")
def contas_financeiras():
    return get_all_pages("/v1/conta-financeira")


@app.get("/centro-custo")
def centro_custo():
    return get_all_pages("/v1/centro-custo")


@app.get("/contas-pagar")
def contas_pagar():
    return get_all_pages("/v1/financeiro/contas-a-pagar")


@app.get("/contas-receber")
def contas_receber():
    return get_all_pages("/v1/financeiro/contas-a-receber")


@app.get("/saldo-bancario")
def saldo_bancario():
    return contaazul_get("/v1/financeiro/saldo-bancario")