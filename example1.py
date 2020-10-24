# import os

from bcncita import CustomerProfile, DocType, Office, OperationType, try_cita

if __name__ == "__main__":
    customer = CustomerProfile(
        anticaptcha_api_key="... your key here ...",  # Anti-captcha API Key (auto_captcha=False to disable it)
        anticaptcha_plugin_path="/Users/username/Downloads/anticaptcha-plugin_v0.50.crx",  # Path to plugin
        auto_captcha=True,  # Enable anti-captcha plugin (if False, you have to solve reCaptcha manualy and press ENTER in the Terminal)
        auto_office=True,
        chrome_driver_path="/usr/local/bin/chromedriver",
        # chrome_profile_name="Profile 7",  # Profile name
        # chrome_profile_path=f"{os.curdir}/chrome_profiles/",  # You can persist Chrome profile between runs, it's good for captcha :)
        fast_forward_url="https://sede.administracionespublicas.gob.es/icpplustieb/acInfo?p=8&tramite=4036&org=AGE",  # Skip first 2 screens by replacing p (city) and tramite
        save_artifacts=True,  # Record available offices / take available slots screenshot
        telegram_token="... your key here ...",  # Your Telegram bot token (sms-confirm cita through a bot using command "/code 12345")
        # wait_exact_time = [
        #     [0, 0], # [minute, second]
        #     [15, 0],
        #     [30, 0],
        #     [45, 0],
        # ],
        # city="Tarragona",
        operation_code=OperationType.RECOGIDA_DE_TARJETA,
        doc_type=DocType.NIE,  # DocType.NIE or DocType.PASSPORT
        doc_value="T1111111R",  # NIE or Passport number, no spaces.
        name="BORIS JOHNSON",  # Your Name
        phone="600000000",  # Phone number (use this format, please)
        email="myemail@here.com",  # Email
        # Offices in order of preference
        # This selects specified offices one by one or a random one if not found.
        # For recogida only the first specified office will be attempted or none
        offices=[Office.BARCELONA_MALLORCA],
    )
    try_cita(context=customer, cycles=100)  # Try 100 times


# In Terminal run:
#   python3 example1.py
