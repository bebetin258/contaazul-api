from fastapi import FastAPI
import requests
import os

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"

BASE64 = "N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts"
REFRESH_TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.s_kwP4CF4yeuU7meajCx5bu44zXSP3cY10V5riAJNpsPbEzD6tX5kGVFkcAXTDrnAYuK5CQecEcXmYYMAe1TNhxL8blIysiQj4te-uVqtNdDptxhJRUREHe_nyC_0bQqRGfILSF-p6m5fvTnSEBhahi7MIFlCAB2je1Y_K2Fy67FwcoSjk5iZcW7hrfOZPbhNElvq8prkvwm9_jgwA2KO8lflCvI-TNpGhADa0XG3JhWfdotqiBtmWMTaF6LLU75gS-b7gB04tksRdboyOWHODASnWid7tX5PCteEzwwi-sI2sUnu93CmocqHC54FIQL0LhbQE0_H69MDtryPWMARw.HVNYeFMMME3ScUTI.wMxQxqaq9QtZYV3IcFpIH-vVyFcHzB_AtaNXocj_e0rMz9m8wyh8qT2_154vKn6WIsjErCHZrMZrc-3Bvor2XP6XsImPBWac8TW-b4eqhi1wUH_qko5CBGsP1ZkhFSVauNO3HGeS2NNy5sT0DSFaiJ0_LRqoY7yK4SDs4VdflXPwqRxuSyoNKywFQ1zHzNJ8X5X8KK_DYXTk3EMsWOICzmqdQtSF-j8y39chVBVn24W849muy7glCx2S2Cm-4tLvf8criAFhyROYMLbl8a0BH44gcY-Cx0ic1X-lS2DRf3-wfmyAlATh9fE34UQXNAV_qc5wG3YoU6ojC0MRZruJUztPe93fLy1GF21mMWi8LDf1peyS4DscueDBfEd-VQ2_vEQuoKaXx0c-FIaydw5gvF2gI-AK4e6mgO7URCUeXOLLqulgFQ1D5Fmf-EogGvWevCaKugjGptEdZij7WERFKk7kRb-__nFMFNz1OcP2wh9LXUpWaDjHwox5JKLRMjhTTZGGy_BwD91cfMJLxNSr-rMN_zJhn7WFNUB-A6v5Vzy98Nw0jVaqTrbruulbRDbKEckqmLWTEshOzvpESV58IsC_2HSs4Vj_R-h3XBb9sFfRnnPwr-RHnZ7DQ8mUxMShkJVKbzgJ4puYcLxqBF2uFi6gizLu_1fMRt9nFaxLM47dj2k_PfZzfmKXbUTlVm-o0ZJA4H6qmhvnYn2mTwM6oOFlkrHERPyQIBX8-o40fxC4U98AgrlFiZdXipAc5xAhuyN3o4L22pEN2Ov21GJgb096nzmYwo2WW5Nzpp8eKDgplksF2xQEFtAZvUXr8T524xdVP3sqpdGhW4I_gWofAmDrYL-rHRzkofSxeedai9bxxWLwwNB48hzc1n5re2DkZpyDQ882gJ5DP7oub81TJkHX6GdVEH68kosf2_sKio3VGMLPcnKKg9l69f4Q0tVTFJ_qvRVyVAxKHv-jWuPryny9VCnsjUkZnB4-ZkNdJ62T_KZ1WAE5zKKtGj_Ob-3ob8nCbZmg-OXSvvfKgodCOlmo7iTg7Sd0lYDZv9rH1OspVa-h4dWzV2se-3ODi17HYD85cuORjJLDp6svCBIJGyjb1Dilv87Nl6jjZXX4PrqIctdYD1bLM-VGCH3XMok54NDncGZ7Bplyo4u7r3ByjC-zWyb-CJgfr9zwj6ADGItMsmdt5dXXHaRCo-pB4eBpuxD2kfpsur1dqs6Pom4IzRyvAkhvTKEFsGV2IKjgVdnDgGEdJyKEYns2_tUYn0-H4EqXQoejTyBD6kVk-XrdwQg90ZmhQmAwkseTT2f2tTxl_BLH2mccS7LQmYtIPoCtJOu1h9O6W4fZOwvrtAIllF0BIN5ufh78BwLAcdgvsR7NDiJubXmArnvoMp4SmmSLSQ.xG1PSRDfyFJyQ-6EfEv_kw"


# =============================
# 🔑 GERAR ACCESS TOKEN
# =============================
def get_access_token():
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
        print("ERRO TOKEN:", response.text)
        raise Exception("Erro ao gerar token")

    return response.json()["access_token"]


# =============================
# 🔄 BUSCAR TODAS AS PÁGINAS
# =============================
def get_all_pages(endpoint):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    pagina = 1
    tamanho = 100
    todos = []

    while True:
        url = f"{BASE_URL}{endpoint}?pagina={pagina}&tamanho_pagina={tamanho}"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("ERRO API:", response.text)
            break

        data = response.json()

        items = data.get("items", [])

        if not items:
            break

        todos.extend(items)

        print(f"Página {pagina} carregada - {len(items)} registros")

        if len(items) < tamanho:
            break

        pagina += 1

    print(f"TOTAL FINAL: {len(todos)}")

    return todos


# =============================
# 🌐 ENDPOINTS
# =============================
@app.get("/")
def home():
    return {"status": "API rodando 🚀"}


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
    return get_all_pages("/v1/contas-a-pagar")


@app.get("/contas-receber")
def contas_receber():
    return get_all_pages("/v1/contas-a-receber")