import requests
from fastapi import FastAPI

app = FastAPI()

BASE_URL = "https://api-v2.contaazul.com"

BASE64 = "N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts"
REFRESH_TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.ovlMLEv2uRRDt6HyY-v7SUaziCpsMTp4ew7EzKYEi66Y0ycgewtLsaoYkvPGT7ykbJWTjvDPXMMChFBpc-tM5dq_DGGIYWd18Jp25QmhCEL9tfDX8wrMHcBMgjgGngOrVcg52ftLX3FhpONy_MOq0X43gtMRlH1U1CKmZeoGyk5lw47S1VAlZq4G1Ks4YLIA5e7fx8giVod0z2I-ukez9hv3Ypv-BIu0XaCzHyIZtL-dG5g6Nc-KNjUTHm6tfO6Z5xCOWg8AqrqjzHtWwWqNsGWVm89FcmoriNcqwr6IMt6xXIVjUQa2cMYOrpBKkAoR4Y3ltT_03z5O6Vb6odk_4Q.3ZUsoT2zTUy6C6TL.TyXy0zBbUpegsKZEH40Aq-ngjrpLukIDShxO-kpNwzodlsnhsCHUgY0k7py-Ilt-8yXueowVTMOsWdLn-OOExe95JXOO6lz5E89vh7sNmadE7PlkgC5KgHE9owh6J5Aotytl2bsXLZHOXwzHkttfZU4mA15Du-sMB-56_dHr3I2aAegM2PBrYbiSh2QJT6p3UHHD-JR4lHK3fUGvtuf7jNtOLj08ApoQ7GyrBarjj4So9KgHFdKDRZI2nYypH2AuENKE8DSS7sSejdOJ_8FlElFt2VqBkxQzcUg_JmeQ9S_TAjdkmg_DBiV46cJdqfs9l-KxI4YPuQZnHDKgHgarS9b9SQ-uTSpeeX7Pez_NZajlT-Wm2nlw6MuEKYV-U0_xHHPtOcijrUT5qgemeyJz5R5tlf10cr6Z77DwQD4YfzuvoBJ8-UMMCVybdhLlJcEizjY6n37XoQZPMBUlVsOxhD17ROOaiw8XJZir7t2vJGrm_KpVf2HW3uwn0HTmKvv1eQbiESEevVeRhCtR5z89VEjQTAMGar7-jnr1zCtEelFfqjLE7CwcgVslZlht67Abq69HyLQVhBnt95qwzLFS2E0rMn9eGuzfuC_4b0r0_u8XVzHJVmymuo_6Rxud-bnYyUkHe4ySZzi-f4-psi2druyiTAGfjK0II8S66hCinifMZIhpS7SaTYQyjZJVBuxIO47sx6RpuT2ZLB7AvXoxLmQHVt2vUnaEwS-pO9MDtyjSbEzHNW3PUxTsfC5mkecqchsGiBntikbW32e4QRaIZpmaPPfLb9f6TMrgbs0vNKQoJ9q7k0nZpS2Boqei7DreiaXed7F2RlsfkTv0LdaMvVqYlG8c0jOe3_Bka49Now1TwXtnc4SLPEYxdQrgxdbZVH_RfYwE3Jw_Ltbbg-7gNh5nviXR6ALIsBTPawr5wwQQencCATN0FRdn2qusjT7UgNYA8NJaI1g14GOxfCLFkSd-FaVT_shTkF9eBVNOTmfxzjA-fUMlD0Gy6EYiTIofgY_INVKazzeFoEWovW15ICGaRCsSdXqiHUO2kS4pm0M-OAPJD0NG-urP3AQa4as6mYLrIbXKHe8YabNuUAMh4D0LnnPBpYgjU1mAWEnMHzEt30KLI_w4pmRPCiBmvqKdaVimY-o-G028pzhYbzgHDsLabp-kGZOVJSJ0ayJT3lX9FTQ9YPF57lZZZ6Qps-8bhJaGLA1HG8FuoL8I2mB1NI75Ixq93s9ki8R8sU4NdXik8pHtF1a6j6SVkgHZ1Yeau4qexJrcPYAWtoX1vmIpBQAQNqA1I-xkcp5mpl-zQXF4DrR2Q4z6YRI6l5M6V78JbW3Hsbv__2GbMjVWPojSmcxg9kNcXxXKSJ0fWbDqjq0ZZzi406QhHvf4ncqzVu2bg2BJbwU._VG-fwRiiL5wLiMXUIGPaA"

ACCESS_TOKEN = None


# =========================
# 🔄 GERAR TOKEN
# =========================

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
        raise Exception(f"Erro ao gerar token: {response.text}")

    token_data = response.json()

    if "access_token" not in token_data:
        raise Exception(f"Token inválido: {token_data}")

    return token_data["access_token"]


# =========================
# 🔗 REQUEST COM RETRY
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

    # 🔥 TOKEN EXPIRADO OU INVALIDO
    if response.status_code == 401 or "Invalid token" in response.text:
        ACCESS_TOKEN = get_access_token()

        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=params
        )

    if response.status_code != 200:
        raise Exception(f"Erro API: {response.text}")

    return response.json()


# =========================
# 📄 PAGINAÇÃO
# =========================

def get_all_pages(endpoint):
    pagina = 1
    resultado = []

    while True:
        data = contaazul_get(
            endpoint,
            params={
                "pagina": pagina,
                "tamanho_pagina": 100
            }
        )

        if "itens" not in data:
            return data

        itens = data["itens"]

        if not itens:
            break

        resultado.extend(itens)
        pagina += 1

    return resultado


# =========================
# 📊 ENDPOINT
# =========================

@app.get("/categorias")
def categorias():
    return get_all_pages("/v1/categorias")