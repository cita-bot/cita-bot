Cita helper
===========

This selenium automatization python script helps to catch cita timeslot. 

**It DOES NOT make a reservation automatically.**

Enable your speakers and wait for "ALARM ALARM ALARM" message :) Next you'll have to select timeslot and confirm an appointment via SMS code.

Installation TL;DR
-------------------

1. Code is specific for MacOS X & Chrome.

2. Install Google Chrome, please.

3. Install Python 3.8: https://www.python.org/downloads/release/python-385/ (macOS 64-bit installer)

4. Get plugin https://antcpt.com/downloads/anticaptcha/chrome/anticaptcha-plugin_v0.50.crx

5. Get API Key from https://Anti-captcha.com (5$ is enough, trust me! :)

6. Copy example file and fill your data, save it as `grab_me.py`.

7. Run `python grab_me.py`, follow the voice instructions.


Examples
--------

* `example1.py` — Recogida de tarjeta

* `example2.py` — Toma de huellas

Options
--------

```
@dataclass
class CustomerProfile:
    name: str
    doc_type: DocType
    doc_value: str  # Passport? "123123123"; Nie? "Y1111111M"

    phone: str
    email: str

    operation_code: OperationType = OperationType.TOMA_HUELLAS
    city: str = "Barcelona"
    country: str = "RUSIA"

    card_expire_date: Optional[str] = None  # "dd/mm/yyyy"
    auto_captcha: bool = True
    auto_pd: bool = True
    selected_pd: Optional[str] = None

    anticaptcha_plugin_path: Optional[str] = None
    api_key: Optional[str] = None
    chrome_profile_path: Optional[str] = None
    chrome_profile_name: Optional[str] = None

```

* `name` — First Lat Name

* `doc_type` — `DocType.NIE` or `DocType.PASSPORT`

* `doc_value` — Document number, no spaces

* `phone` — Phone number, no spaces, like "600000000"

* `email` — Email

* `operation-code` — `OperationType.TOMA_HUELLAS` or `OperationType.RECOGIDA_DE_TARJETA`

* `city` — City name (Barcelona by default). Copy-n-paste using Chrome DevTools from the Select options, please.

* `country` — Country (RUSIA by default). The same copy-n-paste, please.

* `card_expire_date` — Card Expiration Date. Probably, it's not important at all, leave it empty.

* `auto_captcha` — Should we use Anti-Captcha plugin? For a testing purposes, you can disable it and solve reCaptcha by youreslf. Do not click "Enter" or "Accept" buttons, just solve captcha and click Enter in the Terminal.

* `auto_pd` — Automatically choose of the police station. If `False`, again, select an option in the browser manually, do not click "Accept" or "Enter", just click Enter in the Terminal.

* `selected_pd` — Required field for for RECOGIDA_DE_TARJETA! If provided, script will try to select the specific polica station or end the cycle.

* `anticaptcha_plugin_path` — Full path for the plugin file.

* `api_key` — Anti-captcha.com API KEY (not required if auto_captcha=False)

**Chrome Profile Persistent**

It should be easier to resolve captcha if you use Chorme Profile with some history, so it's better to preserver browser history between attempts.

```python
        # chrome_profile_path=f"{os.curdir}/chrome_profiles/",  # You can persist Chrome profile between runs, it's good for captcha :)
        # chrome_profile_name="Profile 7",  # Profile name
```

Try to uncomment this lines in the run script.


How to fix dependencies
------------------------

1. MacOS → Linux. Replace `say` with `espeak`

2. Chrome → Firefox — it's possible as well (tune code, paths, browser run arguments, plugin)