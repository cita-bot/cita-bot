# import os

from bcncita import CustomerProfile, DocType, Office, OperationType, Province, try_cita

if __name__ == "__main__":
    customer = CustomerProfile(
        anticaptcha_api_key="... your key here ...",
        auto_captcha=False,
        auto_office=True,
        chrome_driver_path="/usr/local/bin/chromedriver",
        save_artifacts=True,
        province=Province.BARCELONA,
        operation_code=OperationType.SOLICITUD,
        doc_type=DocType.NIE,
        doc_value="T1111111R",
        country="RUSIA",
        name="BORIS JOHNSON",
        phone="600000000",
        email="myemail@here.com",
        year_of_birth="1980",
        offices=[Office.BARCELONA, Office.MATARO],
    )
    try_cita(context=customer, cycles=200)
