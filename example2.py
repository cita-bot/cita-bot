# import os

from bcncita import CustomerProfile, DocType, OperationType, try_cita

if __name__ == "__main__":
    customer = CustomerProfile(
        # city="Tarragona",
        auto_pd=True,
        auto_captcha=True,
        chrome_driver_path="/usr/local/bin/chromedriver",
        anticaptcha_plugin_path="/Users/username/Downloads/anticaptcha-plugin_v0.50.crx",
        # wait_exact_time = [
        #     [0, 0], # [minute, second]
        #     [15, 0],
        #     [30, 0],
        #     [45, 0],
        # ],
        # chrome_profile_path=f"{os.curdir}/chrome_profiles/",
        # chrome_profile_name="Profile 7",
        operation_code=OperationType.TOMA_HUELLAS,
        api_key="... your key here ...",
        name="BORIS JOHNSON",
        doc_type=DocType.PASSPORT,
        doc_value="1100123123",
        phone="600000000",
        email="myemail@here.com",
    )
    try_cita(context=customer, cycles=100)
