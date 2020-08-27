import os
from bcncita import CustomerProfile, DocType, OperationType, try_cita


if __name__ == "__main__":
    customer = CustomerProfile(
        # city="Tarragona",
        auto_pd=True,
        auto_captcha=True,  # Enable anti-captcha plugin (if False, you have to solve reCaptcha manualy and press ENTER in the Terminal)
        anticaptcha_plugin_path="/Users/username/Downloads/anticaptcha-plugin_v0.50.crx",  # Path to plugin

        # chrome_profile_path=f"{os.curdir}/chrome_profiles/",  # You can persist Chrome profile between runs, it's good for captcha :)
        # chrome_profile_name="Profile 7",  # Profile name

        operation_code=OperationType.RECOGIDA_DE_TARJETA,
        selected_pd="CNP - RAMBLA GUIPUSCOA 74, RAMBLA GUIPUSCOA (74)",  # You have to know exact name of the place

        api_key="... your key here ...",  # Anti-captcha API Key (auto_captcha=False to disable it)
        name="BORIS JOHNSON",  # Your Name
        doc_type=DocType.NIE,  # DocType.NIE or DocType.PASSPORT
        doc_value="T1111111R",  # NIE or Passpoer number, no spaces.
        phone="600000000",  # Phone number (use this format, please)
        email="myemail@here.com",  # Email
    )
    try_cita(context=customer, cycles=100)  # Try 100 times


# In Terminal run:
#   python3 example1.py