Cita helper ![Build Status](https://github.com/cita-bot/cita-bot/actions/workflows/main.yml/badge.svg)
===========

This Selenium automatization script helps to catch cita timeslot.

**It DOES make a reservation (semi)automatically**

...if you [set up a Telegram bot](https://docs.microsoft.com/en-us/azure/bot-service/bot-service-channel-connect-telegram) and use it for SMS confirmation. Otherwise:

Enable your speakers and wait for "ALARM ALARM ALARM" message :) Next you'll have to confirm an appointment via SMS code.

Support notes
-------------

If you want a support for new procedure or province, open an issue or better a pull request.
The following things are fully supported at the moment:

Procedures:
- EXTRANJERIA - SOLICITUD DE AUTORIZACIONES
- POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)
- POLICIA-AUTORIZACIÓN DE REGRESO
- POLICIA-CARTA DE INVITACIÓN
- POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.
- POLICIA-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENCIA Y DE CONCORDANCIA)
- POLICIA-CERTIFICADOS Y ASIGNACION NIE
- POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)
- POLICIA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) Y RENOVACIÓN DE TARJETA DE LARGA DURACIÓN
- POLICÍA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA CIUDADANOS BRITÁNICOS Y SUS FAMILIARES (BREXIT)

Provinces:
- Barcelona
- Santa Cruz de Tenerife

Other provinces are also supported if you leave `offices` empty and that way try and get an appointment in a random office, but if you're required to select a specific office (as in case of `OperationType.RECOGIDA_DE_TARJETA`), you should figure out office ids for your province from the appropriate page on your own.

Installation TL;DR
-------------------

1. Install Python 3.8: https://www.python.org/downloads/release/python-385/

2. `pip install -r requirements.txt`

3. Install Google Chrome.

4. Download [chromedriver](https://chromedriver.chromium.org/downloads) and put it in the PATH (Python dir from step 1 should work).

    4.1. [Windows only] Download [wsay](https://github.com/p-groarke/wsay/releases) and put it in the PATH

5. Get API Key from https://anti-captcha.com ($5 is enough, trust me! :)

6. Copy example file and fill your data, save it as `grab_me.py`.

7. Run `python grab_me.py`, follow the voice instructions.


Examples
--------

* `example1.py` — Recogida de tarjeta

* `example2.py` — Toma de huellas

* `example3.py` — Solicitud de autorizaciones


Options
--------

```python
@dataclass
class CustomerProfile:
    anticaptcha_api_key: Optional[str] = None
    auto_captcha: bool = True
    auto_office: bool = True
    chrome_driver_path: str = None
    chrome_profile_name: Optional[str] = None
    chrome_profile_path: Optional[str] = None
    min_date: Optional[str] = None  # "dd/mm/yyyy"
    max_date: Optional[str] = None  # "dd/mm/yyyy"
    save_artifacts: bool = False
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    wait_exact_time: Optional[list] = None # [[minute, second]]

    province: Province = Province.BARCELONA
    operation_code: OperationType = OperationType.TOMA_HUELLAS
    doc_type: DocType
    doc_value: str  # Passport? "123123123"; Nie? "Y1111111M"
    name: str
    country: str = "RUSIA"
    year_of_birth: Optional[str] = None
    card_expire_date: Optional[str] = None  # "dd/mm/yyyy"
    phone: str
    email: str
    offices: Optional[list] = field(default_factory=list)
    except_offices: Optional[list] = field(default_factory=list)
```

* `anticaptcha_api_key` — Anti-captcha.com API KEY (not required if `auto_captcha=False`)

* `auto_captcha` — Should we use Anti-Captcha? For testing purposes, you can disable it and trick reCaptcha by yourself. Do not select a slot or click buttons, just pretend you're a human reading the page (select text, move cursor etc.) and press Enter in the Terminal.

* `auto_office` — Automatic choice of the police station. If `False`, again, select an option in the browser manually, do not click "Accept" or "Enter", just press Enter in the Terminal.

* `chrome_driver_path` — The path where the chromedriver executable is located. For Linux leave it as it is in the example files. For Windows change it to something like: `chrome_driver_path="C:\\Users\\youruser\\PycharmProjects\\cita-bot\\chromedriver.exe" #This is just an example, put there where you saved the program`.

* `telegram_token` — Telegram bot token for SMS confirmation. Wait for SMS and confirm appointments with a command `/code 12345`. If you do not plan to use Telegram, remove this option.

* `telegram_chat_id` — Telegram chat id for your bot. Can be used along with `telegram_token` to get notified about appointment in case there is no SMS confirmation (sometimes it happens). Chat id can be obtained by sending any message to your bot and checking results at `https://api.telegram.org/bot<TELEGRAM_TOKEN>/getUpdates`

* `min_date` — Minimum date for appointment in "dd/mm/yyyy" format. Appointments available earlier than this date will be skipped.

* `max_date` — Maximium date for appointment in "dd/mm/yyyy" format. Appointments available later than this date will be skipped.

* `wait_exact_time` — Set specific time (minute and second) you want it to hit `Solicitar cita` button

* `province` — Province name (`Province.BARCELONA`, `Province.S_CRUZ_TENERIFE`). [Other provinces](https://github.com/cita-bot/cita-bot/blob/6233b2f5f6a639396f393b69b7bc13f5a631fb1a/bcncita/cita.py#L93-L144).

* `operation_code` — Procedure (`OperationType.AUTORIZACION_DE_REGRESO`, `OperationType.BREXIT`, `OperationType.CARTA_INVITACION`, `OperationType.CERTIFICADOS_NIE`, `OperationType.CERTIFICADOS_NIE_NO_COMUN`, `OperationType.CERTIFICADOS_RESIDENCIA`, `OperationType.CERTIFICADOS_UE`, `OperationType.RECOGIDA_DE_TARJETA`, `OperationType.SOLICITUD`, `OperationType.TOMA_HUELLAS`)

* `doc_type` — `DocType.NIE`, `DocType.PASSPORT` or `DocType.DNI`

* `doc_value` — Document number, no spaces

* `name` — First and Last Name

* `year_of_birth` — Year of birth, like "YYYY"

* `country` — Country (RUSIA by default). Copypaste yours from the appropriate page.

* `card_expire_date` — Card Expiration Date. Probably, it's not important at all, leave it empty.

* `phone` — Phone number, no spaces, like "600000000"

* `email` — Email

* `offices` — Required field for `OperationType.RECOGIDA_DE_TARJETA`! If provided, script will try to select the specific police station or end the cycle. For `OperationType.TOMA_HUELLAS` it attempts to select all provided offices one by one, otherwise selects a random available. [Supported offices](https://github.com/cita-bot/cita-bot/blob/6233b2f5f6a639396f393b69b7bc13f5a631fb1a/bcncita/cita.py#L58-L89)

* `except_offices` — Select offices you would NOT like to get appointment at.

**Chrome Profile Persistence**

It should be easier to resolve captcha if you use Chrome Profile with some history, so it's better to preserve browser history between attempts.

```python
        # chrome_profile_path=f"{os.curdir}/chrome_profiles/",  # You can persist Chrome profile between runs, it's good for captcha :)
        # chrome_profile_name="Profile 7",  # Profile name
```

Try to uncomment these lines in the run script.

Troubleshooting
---------------

For Windows, escape paths with additional backslash, e.g. `C:\\Users\\lehne`

Generate script for Autofill Chrome extension (NOTE: does not work at the moment)
---------------------------------------------------------------------------------

To generate script for [Autofill](https://chrome.google.com/webstore/detail/autofill/nlmmgnhgdeffjkdckmikfpnddkbbfkkk)
extension use `--autofill` option. This approach allows you to forget about captcha.

```bash
$ python grab_me.py --autofill
```
