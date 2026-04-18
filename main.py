from fastapi import FastAPI
import requests
import time

app = FastAPI()

# ==============================
# 🔐 CREDENCIAIS FIXAS (TESTE)
# ==============================
BASE64 = "N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts"

REFRESH_TOKEN = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.kfayTl05UNlkyYygmp2hPE4Jmrvd281yOBtnrIjeKniCSf_65i6EM1epExN_L6oonZNAUUoiiRSfQ1v2AA0Otvn6jta89GS9ytMpoetssxPIPfxI4rLJKBLS_9m9qaS35BFW7weWtxQCxMprq7w9H2SwhFHzT4IoaBLkq193i2NC49RPXUiQZyWqIg0jqx0cK1Kzw4qRtEGaWYPFTbrfDtIpU0c1vyI7Oj0Q_ySC-xF-sR7DyO0v_canF13Y8ZE9Rc4ufbVB8QGRwU00ZL8YACWxfYvYoJf55nv_86v1FaVNmLTKUFYVhmtCpJLlsRu5jybsK38z_GLAJ6rVsXac-w.J7TDMLj-S-L_IoFk.ehFafd89sLQfxst-pDHGTOp08BUCkmmWkgyjuVXOGTjNgbO4vdgqdn4oQIxXMk9KlpYXnf41Fnzwaa-_43OnK9cAAcXE25tFgWC1hiCm16AmiIEtWMUGsI-aifG2z6u9x8St6usOsTevLpr2pA1V0G-vaOG7rIeDN-hsiJDiUAr09iizjxi5Rky0FPE_sMGCgIX20j7mCV1OPY_jNH2zZJGQjIY_UIhjK6WHpRCozbfuBR2k-r0t_znq51jE1xsgfrrGInE58cNjJJ-PtrKyZTxG8me7L9539gu6gkKM0tepmJSkJNFwhcyDruPjGNccJfcDpdWwDen44MoQPMKuu9_To5tRNP-TQSe7dgN7kT1HkTdYg0Eg2hbq0TTWtuNife-jARZccFhATBVxDjvqguVJzIsogdvCRexrDHN77KW5Q2h-K6oduddDnv6Gq1o3bdC9IuGb3NwkhHxVVPr6IXphU75W7N7BeHBxdjzMV-bmedae0GLGGy1lc3eSm0Mzrw4iAH5ChJEY0-Uv_lT35oscxGP55gBuW5-v6zO8cWk2FHywReLSenGE4NF07UOFEKR6squ5UErnkiWwuv63zt_2q9wDTrIezc4uqhB23VCMiqkOEB4evc-Y_iOXAiLJ-OKqTGZLYbHZbw7Iw5A7ZSy2tD_4YbZEveRGRsV0EoGIC6XwbRgVSnamKJZ8dX2v_8AhbMuYfzjRzYePlcMzlf9XeeqoRCyWmz9E6-eT6hwao0X8XI9w6oV1Fx0szDqVHFfz4B4eLXzAWZ3toPYF7xpB6N2oKKFe6wQuXhXMQaU6JANwOtDsYgnBZ4qp2O3Q_noqQIElUWF8761JNcHuzj65id1cHojSCfThmJKn3Uzif3Y-b6orQbn9qsir0A3zAKeim9Eh6Qu6LQDbUtYLY5AfETVz-rXeFW_kAghkDRmgxbnyabPemK8oQu8Zfct5pVecUIX4gs7qgErrLWLLdfB7RaYBLscZ3JMzPAQAosv_-5wmqhqL_FRezZ07uofjaSFLrfhESz6cOhMMqP-0HJi0PyFSMQ8AGBOzNFVCGWA4KafMvHtaj2LUMJ4sFA_RnKgPDmmitIFzdbpYwBBF52cnCE7EfRQg7AW01XqB4AX9sl6w5qt2LBwZbKNuTQCdUI7vB1KFbXN0TTsaoh83jtAW2sEdEvK029GSbpjpoUXb6afHv4uDelzDJOdZCBZ1KQDB9DJeaYAjf5d7xeWsyGKvZ_bLVyJ2nG4qbK649fPp4XZbNjHVXTkmyx50jaYHtU0VKatW6PZaAOLJkr5E2hdpa6YmBTzPPVJJOPxLJEQAK_hP7DbWoxxy4aacEFYdl0NhdvCz2w1MW92KxbtuFI9xYGzlwMgEfimsymy-dh0HqFkEPmWw8A0nIuOru8_17g.BR1vfSqrvgslurCxPxXBHw"

# ==============================
# 🔄 CACHE DE TOKEN
# ==============================
ACCESS_TOKEN = None
TOKEN_EXPIRATION = 0


# ==============================
# 🔑 GERAR TOKEN
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

    print("\n================ TOKEN DEBUG ================")
    print("STATUS:", response.status_code)
    print("RESPOSTA:", response.text)
    print("===========================================\n")

    try:
        data = response.json()
    except:
        raise Exception(f"Resposta inválida: {response.text}")

    if "access_token" not in data:
        raise Exception(f"Erro na autenticação: {data}")

    ACCESS_TOKEN = data["access_token"]
    TOKEN_EXPIRATION = time.time() + data["expires_in"] - 60

    return ACCESS_TOKEN


# ==============================
# 📊 ENDPOINT TESTE
# ==============================
@app.get("/dre-categorias")
def dre_categorias():
    token = get_access_token()

    url = "https://api-v2.contaazul.com/v1/financeiro/categorias-dre"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    print("\n=========== API DEBUG ===========")
    print("STATUS:", response.status_code)
    print("RESPOSTA:", response.text[:500])
    print("================================\n")

    try:
        return response.json()
    except:
        return {
            "erro": "Resposta inválida",
            "status": response.status_code,
            "conteudo": response.text
        }


# ==============================
# 🟢 HEALTH CHECK
# ==============================
@app.get("/")
def home():
    return {"status": "API rodando 🚀"}