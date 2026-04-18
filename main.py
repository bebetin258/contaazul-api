from fastapi import FastAPI
import requests
import os

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"

BASE64 = "N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts"
REFRESH_TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.se5NJmP_QFoxKrdWJWwMJEBoe09TRCHwTzAEtNkSIPpaz8jPeAcwB2ge8ZGh_g62EvcpMOcSB6yoQXQUZ8lA38zdN9UJLc2ky_SXw1dufdZaiqEJnVbQ1aA7QZGHlIsXOnP5WbVCilE9a3qdIlG0oddcFxNKcroMns49JWEfeEYgoI1hdDo8M0Egi7GWGKb_4rwY02DDiemvxkIShBL_OqHWMmEPw6dCe1AcyWsyUqpqu2CbQXAQiKgHVI0Qb60_rGJb2AmLsjfNeTQalT42kPrW6FB7_WR107YxE4Kb_gYizvbQWv5MmJpFnXamUMxceAuXEa16CBM_kA-U8cxJxw.2MfoUYO4bspnn6Dg.ZeEJqo19WGqig50l2_ugex5Q_Lilq89kibzyDzrjBAoNx6zxSk8FNRcxM5tcsRJWMvX2L0A_nnWQJh8iCs_7-b3-wP-u_4yBAbUHcQ7iCx2jB8F2I7sqELjq2dk8T9e8c2wVMPWjRhny_GO5Nlq-5DyLau5lyB-1Y3mrlDb1uh9V7uIIuGXRxxm52tXN0E2HXiX-uYYabvZzAXZzQIZyQp2AqJtxO7kQ8w3GfS2sQ35n2jXnDQMehvX5p3FXKWZK_q3oP2k6fvmYzvQMsJZJh9UF1sNtSBYVPy_0zEexwaOn7YT4riz52q8XZOiyZPU2U9sCRDXA9764exeZ7tm9V1HfBTzorZdEH9Wr1hwamEn6iC0gKvKL39qbv1Fe0AdRBR_U573oDlltWHgOfzdic0pVe7kwB1dpxpgnQnnVvn5WayIOlFnCcoXy6ylmea4_3WJ165tjeFtjxTnjhcQJT1lm9X-BQ5gDBfJ5ZpY96nElXIvzDyhDrDgSEkfCwgba3maoOCfzHzbtXLGG6pGuSaaqzDr-u6lKKQdQ7RmJF1dSuvyVU21Ga6QqC-tsjQcV3wvuvsJE9_7mrwXiYE4Mb4icFmjolmTW-7kYHT-a7q96fpQVN5OoSg-ex-RiMKLBfri6aWzaWzTpvvghAh9LXeMt90Tm736Eaji_kAtrqlYgJEksPwDS3RWxC9TLrXpO_Ic28SdCa24uMn8s_lh0_7qqQfsEE9hZERDaUqWg3UQ2IM6wLa-qroC24xKWCHPhkL-i0cyB60VOsq6w_s2evZz6NySIQTsO8MQp8yKH_dSgbTSvpIcSm98GNeOapG4vKOxOvLDDMsvrROJ0J-drZDBJJ2sOFWYV6GHpqQC7WBz9UvXh7Ci8imit1zzbFTB5SljULA9EXmy-dZ10usgYYuggXkmZumxD7DT2UhTkRI6-PSSl_yxxHnHatLGhKlrXdXxqMV1s9ZCF6ucf6Z1lBltNQ15ZaCxc9TfOJTp8BC4iRMnnG8iE_vX1KiCyBPsD6qWNla14TKgWtKIyni_JMME3-cjiuMcbSmTbxz1gZDqdn03ktsqHtlqLJ8cxJJMvxP7Z8CYNRtuLeSMW031da804NfpDaboOkeAo_bNYan5ANnyHWinqZ1N9rSEkp6Azl1sFS3wvmnL4MKgs2paG8Rd58tVt86Lp1K2wy5c-nDjKpWoL_a_4Ef1Kb0_aKXmn5HEwsnT0azrOBvUYkrcFsRFNeIIwyqTzKrZp085hyMSC91OJ4RkHsC9Bkkt0RuRgNARxgkNmGQ2g8ljLwl37WpR7gu-nSv8FKaV_6KWC5I0Ae1v96FPWou7pQkLiuGPtJ0_43GNVxFOf9vMZh43FFZp1ftpYgxD-kZrPZMRBbKtcnnl4G6Xmlqrp1kyM3dJRhg.lJ8g4Etar4tlV-HI7W2JFA"


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