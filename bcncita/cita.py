import json
import time
import datetime
import os
from enum import Enum
from typing import Optional

from selenium import webdriver

# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from dataclasses import dataclass


__all__ = ["try_cita", "CustomerProfile", "DocType", "OperationType"]


CAPTCHA_TIMEOUT = 180

CYCLES = 100
REFRESH_PAGE_CYCLES = 12

DELAY = 6  # timeout for page load

# SLEEP_PERIOD = 60  # every minute

CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"


class DocType(str, Enum):
    PASSPORT = "passport"
    NIE = "nie"


class OperationType(str, Enum):
    TOMA_HUELLAS = "4010"  # POLICIA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) Y RENOVACIÓN DE TARJETA DE LARGA DURACIÓN
    RECOGIDA_DE_TARJETA = "4036"  # POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)


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


def init_wedriver(context):
    def acp_api_send_request(driver, message_type, data={}):
        message = {
            # this receiver has to be always set as antiCaptchaPlugin
            "receiver": "antiCaptchaPlugin",
            # request type, for example setOptions
            "type": message_type,
            # merge with additional data
            **data,
        }
        # run JS code in the web page context
        # preceicely we send a standard window.postMessage method
        return driver.execute_script(
            """
        return window.postMessage({});
        """.format(
                json.dumps(message)
            )
        )

    options = webdriver.ChromeOptions()

    if context.chrome_profile_path:
        options.add_argument(f"user-data-dir={context.chrome_profile_path}")
    if context.chrome_profile_name:
        options.add_argument(f"profile-directory={context.chrome_profile_name}")
    if context.auto_captcha:
        options.add_extension(context.anticaptcha_plugin_path)

    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
    options

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    browser = webdriver.Chrome(CHROME_DRIVER_PATH, options=options)

    browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    browser.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": ua})

    # https://anti-captcha.com/clients/settings/apisetup
    if context.auto_captcha:
        browser.get("https://antcpt.com/blank.html")
        acp_api_send_request(
            browser, "setOptions", {"options": {"antiCaptchaApiKey": context.api_key}}
        )
        # 3 seconds pause
        time.sleep(1)

    return browser


def try_cita(context: CustomerProfile, cycles: int = CYCLES):
    driver = init_wedriver(context)
    os.system("say Press enter to START")
    print("Press Enter to start")
    input()

    success = False
    for i in range(cycles):
        result = False
        try:
            result = cycle_cita(driver, context)
        except KeyboardInterrupt:
            raise
        except TimeoutException:
            print("Timeout exception")
        except Exception:
            os.system("say SOMETHING BROKEN, press enter or bye")
            print("SMTH BROKEN, press enter")
            input()
            break

        if result:
            success = True
            print("WIN")
            break

    if not success:
        print("FAIL")
        os.system("say FAIL")
        driver.quit()


def toma_hellas_step2(driver: webdriver, context: CustomerProfile):
    # 4. Data form:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtFecha")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    # element = driver.find_element_by_id("txtPaisNac")
    # element.send_keys("S", Keys.UP)
    # element.send_keys("RUS", Keys.ENTER)

    # Select country
    select = Select(driver.find_element_by_id("txtPaisNac"))
    select.select_by_visible_text(context.country)

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element_by_id("rdbTipoDocPas").click()
    elif context.doc_type == DocType.NIE:
        driver.find_element_by_id("rdbTipoDocNie").click()

    # Enter doc number and name
    element = driver.find_element_by_id("txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    if context.card_expire_date:
        element = driver.find_element_by_id("txtFecha")
        element.send_keys(context.card_expire_date)

    success = process_captcha(driver, context)
    if not success:
        return

    # 5. Data confirm:
    time.sleep(0.3)
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "btnEnviar")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    btn = driver.find_element_by_id("btnEnviar")
    btn.send_keys(Keys.ENTER)

    time.sleep(0.5)
    return test_hay_cita_disponible_with_refresh(driver)


def test_hay_cita_disponible_with_refresh(driver: webdriver) -> Optional[bool]:
    resp_text = driver.find_element_by_tag_name("body").text

    if "En este momento no hay citas disponibles" not in resp_text:
        print(f"Cita attempt at {datetime.datetime.now()} hit! :)")
        return True

    for i in range(REFRESH_PAGE_CYCLES):
        time.sleep(5)
        driver.refresh()
        time.sleep(0.5)

        resp_text = driver.find_element_by_tag_name("body").text

        if "En este momento no hay citas disponibles" in resp_text:
            print(f"Cita page refresh attempt at {datetime.datetime.now()}")
        elif "seleccione la provincia donde desea solicitar " in resp_text:
            print(f"Failed step1 attempt after {i} refreshment at {datetime.datetime.now()}")
            return None
        else:
            print(f"Cita attempt at {datetime.datetime.now()} hit! :)")
            return True

    return None


def recogida_de_tarjeta_step2(driver: webdriver, context: CustomerProfile):
    # 4. Data form:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element_by_id("rdbTipoDocPas").click()
    elif context.doc_type == DocType.NIE:
        driver.find_element_by_id("rdbTipoDocNie").click()

    # Enter doc number and name
    element = driver.find_element_by_id("txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    success = process_captcha(driver, context)
    if not success:
        return

    # 5. Data confirm:
    time.sleep(0.3)
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "btnEnviar")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    btn = driver.find_element_by_id("btnEnviar")
    btn.send_keys(Keys.ENTER)

    time.sleep(0.5)

    return test_hay_cita_disponible_with_refresh(driver)


def process_captcha(driver: webdriver, context: CustomerProfile):
    for i in range(1, 4):
        if context.auto_captcha:
            # wait for captcha and proceed:
            WebDriverWait(driver, CAPTCHA_TIMEOUT).until(
                lambda x: x.find_element_by_css_selector(".antigate_solver.solved")
            )
        else:
            print("HEY, FIX CAPTCHA and press ENTER")
            input()
            print("OK, Waiting")

        time.sleep(0.3)

        btn = driver.find_element_by_id("btnEnviar")
        btn.send_keys(Keys.ENTER)

        time.sleep(0.3)
        try:
            WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "btnConsultar")))
            break
        except TimeoutException:
            print("Timed out waiting for page to load after captcha")

        if i == 3:
            # Failed to get catptcha
            print("Failed on success captcha")
            return None
    return True


def cycle_cita(driver: webdriver, context: CustomerProfile):
    driver.get("https://sede.administracionespublicas.gob.es/icpplus/index.html")
    time.sleep(1)  # Let the user actually see something!

    # Select "Barcelona"
    select = Select(driver.find_element_by_id("form"))
    select.select_by_visible_text(context.city)

    btn = driver.find_element_by_id("btnAceptar")
    btn.send_keys(Keys.ENTER)

    # 2. Tramite selection:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "tramiteGrupo[1]")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    select = Select(driver.find_element_by_id("tramiteGrupo[1]"))
    # Select "Huellos"
    select.select_by_value(context.operation_code.value)

    btn = driver.find_element_by_id("btnAceptar")
    btn.send_keys(Keys.ENTER)

    # 3. Instructions page:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "btnEntrar")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    btn = driver.find_element_by_id("btnEntrar")
    btn.send_keys(Keys.ENTER)

    success = False
    if context.operation_code == OperationType.TOMA_HUELLAS:
        success = toma_hellas_step2(driver, context)
    elif context.operation_code == OperationType.RECOGIDA_DE_TARJETA:
        success = recogida_de_tarjeta_step2(driver, context)

    if not success:
        return None

    # =======
    # Stage 2
    # =======

    # 6. PD selection:
    time.sleep(0.3)
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "btnSiguiente")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    if not context.auto_pd:
        os.system("say MAKE A CHOICE")
        print("Press Any Key")
        input()

    if context.selected_pd:
        # Select country
        select = Select(driver.find_element_by_id("idSede"))
        select.select_by_visible_text(context.selected_pd)

    btn = driver.find_element_by_id("btnSiguiente")
    btn.send_keys(Keys.ENTER)

    # 7. phone-mail:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "emailDOS")))
    except TimeoutException:
        print("Timed out waiting for page to load")
        return None

    element = driver.find_element_by_id("txtTelefonoCitado")
    element.send_keys(context.phone)  # phone num

    element = driver.find_element_by_id("emailUNO")
    element.send_keys(context.email)

    element = driver.find_element_by_id("emailDOS")
    element.send_keys(context.email)

    btn = driver.find_element_by_id("btnSiguiente")
    btn.send_keys(Keys.ENTER)

    # Segun Intermediate check
    time.sleep(0.3)

    resp_text = driver.find_element_by_tag_name("body").text

    if "NO HAY SUFICIENTES CITAS" in resp_text:
        print(f"Cita attempt at {datetime.datetime.now()} -> missed second stage :(")
    else:
        print(f"Cita attempt at {datetime.datetime.now()} |-> second stage hit! :)")
        for i in range(10):
            os.system("say ALARM")
        # Wait the hell for my reaction!
        print("Press Any button to CLOSE browser")
        input()

        return True
