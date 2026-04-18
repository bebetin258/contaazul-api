from fastapi import FastAPI
import requests
import os

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"

BASE64 = "N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts"
REFRESH_TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.F-6RN-s_miP68GAbcCmCq9DwZm89nG38JtbXK1TRBVt_5Ys1QuroB2yGEJRo3so-qIfA0qWYZjy2CrhSjly7HTZTCznWh2hpc3ENCfzAhk1SiQP6YITFQngeLC4wEZ_1wyIzuvZJBI9GkJ7NkoDSClHd2S-IXLU5QFZ24FTgrETDJb2-enCFz-Z-09aI5AFUR4SEWFoJMoUFk8Ur0G1lP8lCV3TKSSRkG8F7kArtQsWkoUr9egRhwXDfdFS_vZVNHRxkTuxZlusUpBIF8XQLaLvoRG-Cs2ZSWdnHlz9_20PBTDwnyRGKrfSmh0wfGghu2iAdlalxgndh1tY8lV4vmA.Rz1ffejC_s8HDN6d.lNT-axcIaGEsiRCXLdMsQ6u73r7wxmCJX7_cQcFGSRSZFzMB6It5Hw9HgwhRy8XTfe1g-eRY7JX-yj7uGnET0mQorxOM-VbceJHmXzxZ86pSv6EIVjNDnlT6GOUlBOpg4SLhU2jEYwTvgNEWNnRQZoEvd2YHSO4pySOXmkAN7jccWL89ZVpjrnRYixJqx4yoAdyw3AJDoZjZ7pmfmAsLl2uWeOMb9I_xtB2O4fwT0u8bwhOPjtzqD9nVbVkxax83fj88u9e66Au8CuACcsY6OWWEPLOlkJ9UnbvWJlFpOrvEQ9PxQNLaAfqx1imAOg2i4F1sbHgqGH7HAIoPsv3zvZ3TQFGs6X_jy4AcXA7p9zUYPS7AqwTIndV-iA9rT9WCNc-y7kykrcNEhSFLB-HsaVmJ61tRtZ6_2fTbmV5tUXnR3QQ6LH3NGxBJwwd7e2tqaPWy1FuIlJX_TVNYEiSkMQsspQKGCFfAwQ60gkPKs-Wb-fgam400M64qRfOTO7RnrC3xLdcmKVMN8gMDuECmYkdANxGbvv1cOW5UXY4oNPjoMOjnrKjFdmDwRDEhsOje9bsPvReCUY_3Yuam58HzyTtRLkQWsNZI6iIsAbswMfS4VSataI13kWuiJrZ2hEj9KDE0m0oGV0-iMJv7MCQkDoaiiDQnhDY0RqAgbHlZZIDqQly3SmHnBIMReSb1YFgls_XGohGnUy1-GsyvHYLGapFvD3UIu6Xo20jyGx5figA67s4Sex3LVYfN80FjPKmkCUdTa-AKWD5pJXQi68_HrcgG2g_BgKnOOSNHenHFyIOx1aFRlnZINjL192AhCL2WFeXxNwEvlAu1BuY9mgb0CL1rEKoD8pIVp1aLMtDBjOHNHTwD6bHHJpGoYgXrWA5t8am4rJAfKYxwLLLYR-GF96fnYiT4x3AzijZyHRO4kUXsktekFuSlIMG-422_zb8dOR_9n6_zATWtUDh30HT6f1_2DJdC0qHvnBlOZawHgPkO0h1N8Twewf-qSjeXI6RZ0s4IahCDugV5dGmCOOTy0bnoe3omHcqqitgvxLxrHKd1qi_jl-34_fREC8D1HXA5J-IIntk1sw8mpoeIueWUeX4anMNjdJpZPl5S3BMnzwHtMpaIWKeBvziPhnl7mC5jCtZqgerWzUPE0UFnUkBEx7vSt_5J9F5BPDYAMT6R4Afk3rKMk8bMnD0xl0fhAvmgPLuYIcgP9o6ouJGKL-3kFacjSh4W3-t7sWt-5XiK0xoskMF_b0joE_EDOj_rBIIc3aMBmUZ8aAVZUAarwNl3GoZ25a5DVfRBmYBKr1iAoiyR-g.3dwJq1s-spK5612OOmLm6A"


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