Cita Helper ![Build Status](https://github.com/cita-bot/cita-bot/actions/workflows/main.yml/badge.svg)
===========

This Selenium automatization script helps to catch cita timeslot for Spanish CNP/Extranjería.

Enable your speakers and wait for "ALARM ALARM ALARM" message :) Next you'll have to confirm an appointment via SMS code.

It can make a reservation automatically if you set up anti-captcha, webhooks and IFTTT applet on your phone, read instructions below.


Support notes
-------------

If you want a support for new procedure or province, open an issue or better a pull request.
The following things are fully supported at the moment:

Procedures:
- POLICIA - SOLICITUD ASILO
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

1. Install [Python 3.10](https://www.python.org/downloads/release/python-3100/).

2. `pip install -r requirements.txt`

3. Install Google Chrome.

4. Download [chromedriver](https://chromedriver.chromium.org/downloads) and put it in the PATH (Python dir from step 1 should work).

    4.1. [Windows only] Download [wsay](https://github.com/p-groarke/wsay/releases) and put it in the PATH.

5. Copy example file and fill your data, save it as `grab_me.py`.

6. Run `python grab_me.py` or `python3 grab_me.py`, follow the voice instructions.

### Optional steps for automation:

7. Get API key from https://anti-captcha.com ($5 is enough, trust me! :) and set `auto_captcha=True`.

8. Get API key from https://webhook.site and set it to `sms_webhook_token`.

9. Install [IFTTT](https://ifttt.com/) or any other automation tool on your phone and create an applet redirecting SMS having text "CITA PREVIA" to the temporary email you got from https://webhook.site.

Examples
--------

* `example1.py` — Recogida de tarjeta

* `example2.py` — Toma de huellas

Options
--------

```python
@dataclass
class CustomerProfile:
    anticaptcha_api_key: Optional[str] = None
    auto_captcha: bool = True
    auto_office: bool = True
    chrome_driver_path: str = None
    min_date: Optional[str] = None  # "dd/mm/yyyy"
    max_date: Optional[str] = None  # "dd/mm/yyyy"
    save_artifacts: bool = False
    sms_webhook_token: Optional[str] = None
    wait_exact_time: Optional[list] = None # [[minute, second]]

    province: Province = Province.BARCELONA
    operation_code: OperationType = OperationType.TOMA_HUELLAS
    doc_type: DocType
    doc_value: str  # Passport? "123123123"; Nie? "Y1111111M"
    name: str
    country: str = "RUSIA"
    year_of_birth: Optional[str] = None
    phone: str
    email: str
    offices: Optional[list] = field(default_factory=list)
    except_offices: Optional[list] = field(default_factory=list)
    reason_or_type: str = "solicitud de asilo"
```

* `anticaptcha_api_key` — Anti-captcha.com API key (not required if `auto_captcha=False`)

* `auto_captcha` — Should we use Anti-Captcha? For testing purposes, you can disable it and trick reCaptcha by yourself. While on appointment selection page, do not select a slot or click buttons, just pretend you're a human reading the page (select text, move cursor etc.) and press Enter in the Terminal.

* `auto_office` — Automatic choice of the police station. If `False`, again, select an option in the browser manually, do not click "Accept" or "Enter", just press Enter in the Terminal.

* `chrome_driver_path` — The path where the chromedriver executable is located. For Linux leave it as it is in the example files. For Windows change it to something like: `chrome_driver_path="C:\\Users\\youruser\\AppData\\Local\\Programs\\Python\\Python38-32\\chromedriver.exe",` This is just an example, enter the path where you saved the program.

* `min_date` — Minimum date for appointment in "dd/mm/yyyy" format. Appointments available earlier than this date will be skipped.

* `max_date` — Maximium date for appointment in "dd/mm/yyyy" format. Appointments available later than this date will be skipped.

* `sms_webhook_token` — webhook.site API key, used to automate SMS confirmation.

* `wait_exact_time` — Set specific time (minute and second) you want it to hit `Solicitar cita` button

* `province` — Province name (`Province.BARCELONA`, `Province.S_CRUZ_TENERIFE`). [Other provinces](https://github.com/cita-bot/cita-bot/blob/6233b2f5f6a639396f393b69b7bc13f5a631fb1a/bcncita/cita.py#L93-L144).

* `operation_code` — Procedure (`OperationType.TOMA_HUELLAS`). [All procedures](https://github.com/cita-bot/cita-bot/blob/9217b485e5f2ff35ef2ed8083fcc8a4606c8be0a/bcncita/cita.py#L47-L57).

* `doc_type` — `DocType.NIE`, `DocType.PASSPORT` or `DocType.DNI`

* `doc_value` — Document number, no spaces

* `name` — First and Last Name

* `year_of_birth` — Year of birth, like "YYYY"

* `country` — Country (RUSIA by default). Copypaste yours from the appropriate page.

* `phone` — Phone number, no spaces, like "600000000"

* `email` — Email

* `offices` — Required field for `OperationType.RECOGIDA_DE_TARJETA`! If provided, script will try to select the specific police station or end the cycle. For `OperationType.TOMA_HUELLAS` it attempts to select all provided offices one by one, otherwise selects a random available. [Supported offices](https://github.com/cita-bot/cita-bot/blob/6233b2f5f6a639396f393b69b7bc13f5a631fb1a/bcncita/cita.py#L58-L89).

* `except_offices` — Select offices you would NOT like to get appointment at.

* `reason_or_type` — "Motivo o tipo de solicitud de la cita". Required for some cases, like `OperationType.SOLICITUD_ASILO`. [Related blog post](https://blogextranjeriaprogestion.org/2018/05/14/cita-previa-tramites-asilo-pradillo/).

Troubleshooting
---------------

For Windows, escape paths with additional backslash, e.g. `C:\\Users\\lehne`

If you feel like the script is being stuck at the office selection page — it's not, it refreshes the page 12 times (maximum allowed) until the office is found and then starts over.

SMTH BROKEN: [Errno 13] — that means the script is unable to write a file to file system, try to adjust permissions for it, or set `save_artifacts=False` to disable saving snapshots for offices/appointments.

Generate script for Autofill Chrome extension (NOTE: does not work at the moment)
---------------------------------------------------------------------------------

To generate script for [Autofill](https://chrome.google.com/webstore/detail/autofill/nlmmgnhgdeffjkdckmikfpnddkbbfkkk)
extension use `--autofill` option. This approach allows you to forget about captcha.

```bash
$ python grab_me.py --autofill
```
