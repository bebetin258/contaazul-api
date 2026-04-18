from fastapi import FastAPI
import requests
import time
import os

app = FastAPI()

# 🔐 você pode colocar como variável de ambiente no Render depois
BASE64 = os.getenv("N2xpOGlqdjJiYWJiYm05dHBtMzk4djBqOTE6ZGQ0Y2s5YjA1bWJsb285MjF0M2dwdWQ4YWtuMzFtdTk3YnIzOWhkbGZvYjhmYzd2Ymts")  # ou colar direto aqui se quiser
REFRESH_TOKEN = os.getenv("eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.VjPywOSBRjS4sTteoaw2JhUkYMF2-_V4N34cMRY0bWHXlhGxyAWhA0A4dL3zwbaPwJuGJgXeRE8Kq8Vc2wUEqxXgGgIYpa_3X_dG7w4SVkNlzypTEHGBz7L6rZir4j9H1rGFQuGGItkq1YC2nZDWvQwX6Gd9AbASkf3AahaHnnosl9HEIeFPmQjIsffvvPApeaiCgcTP3F4ZYC12u1e9PmFJLGCNpQHO2-6x9yUkjhTMyyC9Mk3sZCBS8E5vWTuDfS-X5tHotVRq_5N6tTJ8Kds8qiKzmn0UnEBJAXSQvzbc1Ru3bHZkZQ2PhcPB32F-VGX_OE1Z_MUQKG1VsSsQGg.noEejNBO66mu02zU.xQNv48tedxqLPX7jHJBx29uPYPDfv60kFrWK4pyJ6tbd6wEWjo7QGXLEzzKeOWwsldbCgoeGLxwXifxCpv2BxrXU0Rm5TnYIzmPpvmHvwRBnMrwec1od0dQDD-p68WpgnKCvPmBQTJ5BnV6CGA4S5-vxQ9JptAFG3Df_GA_rvmtas8pI0H7eirGQOMpHJ2XwGDMZT3ojfwY-ceosVmGV1LeoekXocnT7zz1iwxyAMa21EMviwPXw_bR3XNYYKGFJNfpcr49g-RBIxhP3Ny-lM_ypepNr7One30cpAeMItJ4gC5tm7POxXHwKV54wK2RyjfaOIdHqDmg4As-7Kb8th4cnnVx_fkgX4vaZ65yHnSAAlxDFsoqy2dHra3U8KW3OER7Z5OdMy4n8gfLpqDOcLxMNUPDP1xwk0oXU4FIE_cUP4vsxLgJVOo5hhibLFJdZtPyHp_nlleB5mU6cdQCJ3j5sxBT3C3lRrWUbn7h-swdHSdqsyfnKiKGgXgXtvFty39ZBBOdK1EIV-xAsFrkZS2Qz-ujXzcA4Y68Svadal8BA6PC93RICItkl_K3RCVHSrrMdNLqkO8V_or0l3qGQFEVdFFI_VSu5Yi1tRGf4LNGE3jTupg6zwcmy2CsuW69VY9dM-uEsuyjPRLgD77ztvMW-CCYfPJiEJKnIgzBDYACi_MWFo-TgQLUCy9xXCAc5OpVwhM2EAj-knxgaTzgSu_RTrpCsN1l0-_G14wGN9Ro-GA6da-8QSuJN0fnGs8Rc17XUsSImJBwK_XIcj6hZigjR2p8J6QFQ_XOCH8HFikfRRAYvJDRYOkVlyNAnXKjIhhxXM9A2dr50zWflNB0EX-PtlTcwg1dOukXYHsFPGPuLtr06YSviQlpM9LgJlTOmbm2ozs3jbpP2d5in1_zDtZoYvURQZQhA6yrcOQ9li6DvZrAPrutXmPh_ZG5ps3GrD0RsZeBn0g3a9HseCGb2ocPP43iR_grgJnYjP3Aa9UEj_4mo5ES43j67-IIvoIA6g2I5f2AgmTdrJ_YSY2J9X1LlWSlVdVustpiZxFVKXlP5hnLbY3PI35ECt0oe1ibI1-E774bOT8OswJdE6VMBIo77NFUIR5dZPfIV7rBoxRLbB_ig7zlnoy-3ewuTPyTIHKyWuo_ik14w7FUKUNkp7vllWea7JaPYBG3ctWdun7W5dvlnlUfIvbcCmWAsmuwsNGSmC0OHlZPlXnSU9-DqGDo9YJd88VWjwXU-Sjj4Z-F4JAG8Q08-wYwAlxR3ppjNqTYUeb6NHEPwoPvR7Ol2OuHeovt1vKYYVi73-Ef-upL3GTkSDz_8M3nVy0Zw9xs1OfbnHTDKrt9UTnvEI5YQ9blwsvQGjIP3l715I5s6ym0UFFcU5xwAe6CijgHiOy8TKg.MCUPU_1gbq2OSPbuE6cPqw")

ACCESS_TOKEN = None
TOKEN_EXPIRATION = 0

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

    print("TOKEN STATUS:", response.status_code)

    data = response.json()

    ACCESS_TOKEN = data["access_token"]
    TOKEN_EXPIRATION = time.time() + data["expires_in"] - 60

    return ACCESS_TOKEN


@app.get("/")
def home():
    return {"status": "ok"}


@app.get("/dre-categorias")
def dre_categorias():
    token = get_access_token()

    url = "https://api-v2.contaazul.com/v1/financeiro/categorias-dre"

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )

    return response.json()