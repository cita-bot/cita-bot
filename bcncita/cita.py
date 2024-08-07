import io
import json
import logging
import os
import random
import re
import sys
import tempfile
import time
from base64 import b64decode
from dataclasses import dataclass, field
from datetime import datetime as dt
from enum import Enum
from json.decoder import JSONDecodeError
from typing import Any, Dict, Optional

import backoff
import requests
from anticaptchaofficial.imagecaptcha import imagecaptcha
from anticaptchaofficial.recaptchav3proxyless import recaptchaV3Proxyless
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from .speaker import new_speaker

__all__ = [
    "try_cita",
    "start_with",
    "init_wedriver",
    "CustomerProfile",
    "DocType",
    "OperationType",
    "Office",
    "Province",
]

CYCLES = 144
REFRESH_PAGE_CYCLES = 12

DELAY = 30  # timeout for page load

speaker = new_speaker()


class DocType(str, Enum):
    DNI = "dni"
    NIE = "nie"
    PASSPORT = "passport"


class OperationType(str, Enum):
    AUTORIZACION_DE_REGRESO = "20"  # POLICIA-AUTORIZACIÓN DE REGRESO
    BREXIT = "4094"  # POLICÍA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA CIUDADANOS BRITÁNICOS Y SUS FAMILIARES (BREXIT)
    CARTA_INVITACION = "4037"  # POLICIA-CARTA DE INVITACIÓN
    CERTIFICADOS_NIE = "4096"  # POLICIA-CERTIFICADOS Y ASIGNACION NIE
    CERTIFICADOS_NIE_NO_COMUN = "4079"  # POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)
    CERTIFICADOS_RESIDENCIA = "4049"  # POLICIA-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENCIA Y DE CONCORDANCIA) #fmt: off
    CERTIFICADOS_UE = "4038"  # POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.
    RECOGIDA_DE_TARJETA = "4036"  # POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)
    SOLICITUD_ASILO = "4078"  # POLICIA - SOLICITUD ASILO
    TOMA_HUELLAS = "4010"  # POLICIA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) Y RENOVACIÓN DE TARJETA DE LARGA DURACIÓN
    ASIGNACION_NIE = "4031"  # Asignación de N.I.E.
    FINGERP_RINT = "4047"  # POLICÍA-EXPEDICIÓN DE TARJETAS CUYA AUTORIZACIÓN RESUELVE LA DIRECCIÓN GENERAL DE MIGRACIONES


class Office(str, Enum):
    # Barcelona
    BADALONA = "18"  # CNP-COMISARIA BADALONA, AVDA. DELS VENTS (9)
    BARCELONA = "16"  # CNP - RAMBLA GUIPUSCOA 74, RAMBLA GUIPUSCOA (74)
    BARCELONA_MALLORCA = "14"  # CNP MALLORCA-GRANADOS, MALLORCA (213)
    CASTELLDEFELS = "19"  # CNP-COMISARIA CASTELLDEFELS, PLAÇA DE L`ESPERANTO (4)
    CERDANYOLA = "20"  # CNP-COMISARIA CERDANYOLA DEL VALLES, VERGE DE LES FEIXES (4)
    CORNELLA = "21"  # CNP-COMISARIA CORNELLA DE LLOBREGAT, AV. SANT ILDEFONS, S/N
    ELPRAT = "23"  # CNP-COMISARIA EL PRAT DE LLOBREGAT, CENTRE (4)
    GRANOLLERS = "28"  # CNP-COMISARIA GRANOLLERS, RICOMA (65)
    HOSPITALET = "17"  # CNP-COMISARIA L`HOSPITALET DE LLOBREGAT, Rbla. Just Oliveres (43)
    IGUALADA = "26"  # CNP-COMISARIA IGUALADA, PRAT DE LA RIBA (13)
    MANRESA = "38"  # CNP-COMISARIA MANRESA, SOLER I MARCH (5)
    MATARO = "27"  # CNP-COMISARIA MATARO, AV. GATASSA (15)
    MONTCADA = "31"  # CNP-COMISARIA MONTCADA I REIXAC, MAJOR (38)
    RIPOLLET = "32"  # CNP-COMISARIA RIPOLLET, TAMARIT (78)
    RUBI = "29"  # CNP-COMISARIA RUBI, TERRASSA (16)
    SABADELL = "30"  # CNP-COMISARIA SABADELL, BATLLEVELL (115)
    SANTACOLOMA = "35"  # CNP-COMISARIA SANTA COLOMA DE GRAMENET, IRLANDA (67)
    SANTADRIA = "33"  # CNP-COMISARIA SANT ADRIA DEL BESOS, AV. JOAN XXIII (2)
    SANTBOI = "24"  # CNP-COMISARIA SANT BOI DE LLOBREGAT, RIERA BASTÉ (43)
    SANTCUGAT = "34"  # CNP-COMISARIA SANT CUGAT DEL VALLES, VALLES (1)
    SANTFELIU = "22"  # CNP-COMISARIA SANT FELIU DE LLOBREGAT, CARRERETES (9)
    TERRASSA = "36"  # CNP-COMISARIA TERRASSA, BALDRICH (13)
    VIC = "37"  # CNP-COMISARIA VIC, BISBE MORGADES (4)
    VILADECANS = "25"  # CNP-COMISARIA VILADECANS, AVDA. BALLESTER (2)
    VILAFRANCA = "46"  # CNP COMISARIA VILAFRANCA DEL PENEDES, Avinguda Ronda del Mar, 109
    VILANOVA = "39"  # CNP-COMISARIA VILANOVA I LA GELTRU, VAPOR (19)

    # Tenerife
    OUE_SANTA_CRUZ = "1"  # 1 OUE SANTA CRUZ DE TENERIFE,  C/LA MARINA, 20
    PLAYA_AMERICAS = "2"  # CNP-Playa de las Américas, Av. de los Pueblos, 2
    PUERTO_CRUZ = "3"  # CNP-Puerto de la Cruz/Los Realejos, Av. del Campo y Llarena, 3


class Province(str, Enum):
    A_CORUÑA = "15"
    ALBACETE = "2"
    ALICANTE = "3"
    ALMERÍA = "4"
    ARABA = "1"
    ASTURIAS = "33"
    ÁVILA = "5"
    BADAJOZ = "6"
    BARCELONA = "8"
    BIZKAIA = "48"
    BURGOS = "9"
    CÁCERES = "10"
    CÁDIZ = "11"
    CANTABRIA = "39"
    CASTELLÓN = "12"
    CEUTA = "51"
    CIUDAD_REAL = "13"
    CÓRDOBA = "14"
    CUENCA = "16"
    GIPUZKOA = "20"
    GIRONA = "17"
    GRANADA = "18"
    GUADALAJARA = "19"
    HUELVA = "21"
    HUESCA = "22"
    ILLES_BALEARS = "7"
    JAÉN = "23"
    LA_RIOJA = "26"
    LAS_PALMAS = "35"
    LEÓN = "24"
    LLEIDA = "25"
    LUGO = "27"
    MADRID = "28"
    MÁLAGA = "29"
    MELILLA = "52"
    MURCIA = "30"
    NAVARRA = "31"
    ORENSE = "32"
    PALENCIA = "34"
    PONTEVEDRA = "36"
    SALAMANCA = "37"
    S_CRUZ_TENERIFE = "38"
    SEGOVIA = "40"
    SEVILLA = "41"
    SORIA = "42"
    TARRAGONA = "43"
    TERUEL = "44"
    TOLEDO = "45"
    VALENCIA = "46"
    VALLADOLID = "47"
    ZAMORA = "49"
    ZARAGOZA = "50"


@dataclass
class CustomerProfile:
    name: str
    doc_type: DocType
    doc_value: str  # Passport? "123123123"; Nie? "Y1111111M"
    phone: str
    email: str
    province: Province = Province.BARCELONA
    operation_code: OperationType = OperationType.TOMA_HUELLAS
    country: str = "RUSIA"
    year_of_birth: Optional[str] = None
    offices: Optional[list] = field(default_factory=list)
    except_offices: Optional[list] = field(default_factory=list)

    anticaptcha_api_key: Optional[str] = None
    auto_captcha: bool = True
    auto_office: bool = True
    chrome_driver_path: str = "/usr/local/bin/chromedriver"
    chrome_profile_name: Optional[str] = None
    chrome_profile_path: Optional[str] = None
    min_date: Optional[str] = None  # "dd/mm/yyyy"
    max_date: Optional[str] = None  # "dd/mm/yyyy"
    min_time: Optional[str] = None  # "hh:mm"
    max_time: Optional[str] = None  # "hh:mm"
    save_artifacts: bool = False
    sms_webhook_token: Optional[str] = None
    wait_exact_time: Optional[list] = None  # [[minute, second]]
    reason_or_type: str = "solicitud de asilo"

    # Internals
    bot_result: bool = False
    first_load: Optional[bool] = True  # Wait more on the first load to cache stuff
    log_settings: Optional[dict] = field(default_factory=lambda: {"stream": sys.stdout})
    recaptcha_solver: Any = None
    image_captcha_solver: Any = None
    current_solver: Any = None

    def __post_init__(self):
        if self.operation_code == OperationType.RECOGIDA_DE_TARJETA:
            assert len(self.offices) == 1, "Indicate the office where you need to pick up the card"


def init_wedriver(context: CustomerProfile):
    options = webdriver.ChromeOptions()

    if context.chrome_profile_path:
        options.add_argument(f"user-data-dir={context.chrome_profile_path}")
    if context.chrome_profile_name:
        options.add_argument(f"profile-directory={context.chrome_profile_name}")

    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"

    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--disable-gpu")

    settings = {
        "recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
    }
    prefs = {
        "printing.print_preview_sticky_settings.appState": json.dumps(settings),
        "download.default_directory": os.getcwd(),
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--kiosk-printing")

    browser = webdriver.Chrome(context.chrome_driver_path, options=options)
    browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    browser.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": ua})

    return browser


def try_cita(context: CustomerProfile, cycles: int = CYCLES):
    driver = init_wedriver(context)
    start_with(driver, context, cycles)


def start_with(driver: webdriver, context: CustomerProfile, cycles: int = CYCLES):
    logging.basicConfig(
        format="%(asctime)s - %(message)s", level=logging.INFO, **context.log_settings  # type: ignore
    )
    if context.sms_webhook_token:
        delete_message(context.sms_webhook_token)

    operation_category = "icpplus"
    operation_param = "tramiteGrupo[1]"

    if context.province == Province.BARCELONA:
        operation_category = "icpplustieb"
        operation_param = "tramiteGrupo[0]"
    elif context.province in [
        Province.ALICANTE,
        Province.ILLES_BALEARS,
        Province.LAS_PALMAS,
        Province.S_CRUZ_TENERIFE,
    ]:
        operation_category = "icpco"
    elif context.province == Province.MADRID:
        operation_category = "icpplustiem"
    elif context.province == Province.MÁLAGA:
        operation_category = "icpco"
        operation_param = "tramiteGrupo[0]"
    elif context.province in [
        Province.MELILLA,
        Province.SEVILLA,
    ]:
        operation_param = "tramiteGrupo[0]"

    fast_forward_url = "https://icp.administracionelectronica.gob.es/{}/citar?p={}".format(
        operation_category, context.province
    )
    fast_forward_url2 = "https://icp.administracionelectronica.gob.es/{}/acInfo?{}={}".format(
        operation_category, operation_param, context.operation_code
    )

    success = False
    result = False
    for i in range(cycles):
        try:
            logging.info(f"\033[33m[Attempt {i + 1}/{cycles}]\033[0m")
            result = cycle_cita(driver, context, fast_forward_url, fast_forward_url2)
        except KeyboardInterrupt:
            raise
        except TimeoutException:
            logging.error("Timeout exception")
        except Exception as e:
            logging.error(f"SMTH BROKEN: {e}")
            continue

        if result:
            success = True
            logging.info("WIN")
            break

    if not success:
        logging.error("FAIL")
        speaker.say("FAIL")
        driver.quit()


def toma_huellas_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtPaisNac")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select country
    select = Select(driver.find_element(By.ID, "txtPaisNac"))
    select.select_by_visible_text(context.country)

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    return True


def recogida_de_tarjeta_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    return True


def solicitud_asilo_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name, Keys.TAB, context.year_of_birth)

    # Select country
    select = Select(driver.find_element(By.ID, "txtPaisNac"))
    select.select_by_visible_text(context.country)

    return True


def brexit_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    return True


def carta_invitacion_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.DNI:
        driver.find_element(By.ID, "rdbTipoDocDni").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    return True


def certificados_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.DNI:
        driver.find_element(By.ID, "rdbTipoDocDni").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    return True


def autorizacion_de_regreso_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    return True


def asignacion_nie_step2(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        option = driver.find_element(By.ID, "rdbTipoDocPas")
        if option:
            option.send_keys(Keys.SPACE)

    # Enter doc number, name and year of birth
    element = driver.find_element(By.ID, "txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name, Keys.TAB, context.year_of_birth)

    # Select country
    select = Select(driver.find_element(By.ID, "txtPaisNac"))
    select.select_by_visible_text(context.country)

    return True


def wait_exact_time(driver: webdriver, context: CustomerProfile):
    if context.wait_exact_time:
        WebDriverWait(driver, 1200).until(
            lambda _x: [dt.now().minute, dt.now().second] in context.wait_exact_time
        )


def body_text(driver: webdriver):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return driver.find_element(By.TAG_NAME, "body").text
    except TimeoutException:
        logging.info("Timed out waiting for body to load")
        return ""


def process_captcha(driver: webdriver, context: CustomerProfile):
    if context.auto_captcha:
        if not context.anticaptcha_api_key:
            logging.error("Anticaptcha API key is empty")
            return None

        if len(driver.find_elements(By.ID, "reCAPTCHA_site_key")) > 0:
            captcha_result = solve_recaptcha(driver, context)
        elif len(driver.find_elements(By.CSS_SELECTOR, "img.img-thumbnail")) > 0:
            captcha_result = solve_image_captcha(driver, context)
        else:
            captcha_result = True

        if not captcha_result:
            return None

    else:
        logging.info(
            "HEY, DO SOMETHING HUMANE TO TRICK THE CAPTCHA (select text, move cursor etc.) and press ENTER"
        )
        for i in range(10):
            speaker.say("ALARM")
        input()

    return True


def solve_recaptcha(driver: webdriver, context: CustomerProfile):
    if not context.recaptcha_solver:
        site_key = driver.find_element(By.ID, "reCAPTCHA_site_key").get_attribute("value")
        page_action = driver.find_element(By.ID, "action").get_attribute("value")
        logging.info("Anticaptcha: site key: " + site_key)
        logging.info("Anticaptcha: action: " + page_action)

        context.recaptcha_solver = recaptchaV3Proxyless()
        context.recaptcha_solver.set_verbose(1)
        context.recaptcha_solver.set_key(context.anticaptcha_api_key)
        context.recaptcha_solver.set_website_url("https://icp.administracionelectronica.gob.es")
        context.recaptcha_solver.set_website_key(site_key)
        context.recaptcha_solver.set_page_action(page_action)
        context.recaptcha_solver.set_min_score(0.9)

    context.current_solver = type(context.recaptcha_solver)

    g_response = context.recaptcha_solver.solve_and_return_solution()
    if g_response != 0:
        logging.info("Anticaptcha: g-response: " + g_response)
        driver.execute_script(
            f"document.getElementById('g-recaptcha-response').value = '{g_response}'"
        )
        return True
    else:
        logging.error("Anticaptcha: " + context.recaptcha_solver.err_string)
        return None


def solve_image_captcha(driver: webdriver, context: CustomerProfile):
    if not context.image_captcha_solver:
        context.image_captcha_solver = imagecaptcha()
        context.image_captcha_solver.set_verbose(1)
        context.image_captcha_solver.set_key(context.anticaptcha_api_key)

    context.current_solver = type(context.image_captcha_solver)

    try:
        img = driver.find_elements(By.CSS_SELECTOR, "img.img-thumbnail")[0]
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(b64decode(img.get_attribute("src").split(",")[1].strip()))
        tmp.close()

        captcha_result = context.image_captcha_solver.solve_and_return_solution(tmp.name)
        if captcha_result != 0:
            logging.info("Anticaptcha: captcha text: " + captcha_result)
            element = driver.find_element(By.ID, "captcha")
            element.send_keys(captcha_result)
            return True
        else:
            logging.error("Anticaptcha: " + context.image_captcha_solver.err_string)
            return None
    finally:
        os.unlink(tmp.name)


def find_best_date_slots(driver: webdriver, context: CustomerProfile):
    try:
        els = driver.find_elements(By.CSS_SELECTOR, "[id^=lCita_]")
        dates = sorted([*map(lambda x: x.text, els)])
        best_date = find_best_date(dates, context)
        if best_date:
            return dates.index(best_date) + 1
    except Exception as e:
        logging.error(e)

    return None


def find_best_date(dates, context: CustomerProfile):
    if not context.min_date and not context.max_date:
        return dates[0]

    pattern = re.compile(r"\d{2}/\d{2}/\d{4}")
    date_format = "%d/%m/%Y"

    for date in dates:
        try:
            found = pattern.findall(date)[0]
            if found:
                appt_date = dt.strptime(found, date_format)
                if context.min_date:
                    if appt_date < dt.strptime(context.min_date, date_format):
                        continue
                if context.max_date:
                    if appt_date > dt.strptime(context.max_date, date_format):
                        continue

                return date
        except Exception as e:
            logging.error(e)
            continue

    logging.info(
        f"Nothing found for dates {context.min_date} - {context.max_date}, {context.min_time} - {context.max_time}, skipping"
    )
    return None


def select_office(driver: webdriver, context: CustomerProfile):
    if not context.auto_office:
        speaker.say("MAKE A CHOICE")
        logging.info("Select office and press ENTER")
        input()
        return True
    else:
        el = driver.find_element(By.ID, "idSede")
        select = Select(el)
        if context.save_artifacts:
            offices_path = os.path.join(os.getcwd(), f"offices-{dt.now()}.html".replace(":", "-"))
            with io.open(offices_path, "w", encoding="utf-8") as f:
                f.write(el.get_attribute("innerHTML"))

        if context.offices:
            for office in context.offices:
                try:
                    select.select_by_value(office.value)
                    return True
                except Exception as e:
                    logging.error(e)
                    if context.operation_code == OperationType.RECOGIDA_DE_TARJETA:
                        return None

        for i in range(5):
            options = list(filter(lambda o: o.get_attribute("value") != "", select.options))
            default_count = len(select.options)
            first_element = 0 if len(options) == default_count else 1
            select.select_by_index(random.randint(first_element, default_count - 1))
            if el.get_attribute("value") not in context.except_offices:  # type: ignore
                return True
            continue

        return None


def office_selection(driver: webdriver, context: CustomerProfile):
    driver.execute_script("enviar('solicitud');")

    for i in range(REFRESH_PAGE_CYCLES):
        resp_text = body_text(driver)

        if "Seleccione la oficina donde solicitar la cita" in resp_text:
            logging.info("[Step 2/6] Office selection")

            # Office selection:
            time.sleep(0.3)
            try:
                WebDriverWait(driver, DELAY).until(
                    EC.presence_of_element_located((By.ID, "btnSiguiente"))
                )
            except TimeoutException:
                logging.error("Timed out waiting for offices to load")
                return None

            res = select_office(driver, context)
            if res is None:
                time.sleep(5)
                driver.refresh()
                continue

            btn = driver.find_element(By.ID, "btnSiguiente")
            btn.send_keys(Keys.ENTER)
            return True
        elif "En este momento no hay citas disponibles" in resp_text:
            time.sleep(5)
            driver.refresh()
            continue
        else:
            logging.info("[Step 2/6] Office selection -> No offices")
            return None


def phone_mail(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(
            EC.presence_of_element_located((By.ID, "txtTelefonoCitado"))
        )
        logging.info("[Step 3/6] Contact info")
    except TimeoutException:
        logging.error("Timed out waiting for contact info page to load")
        return None

    element = driver.find_element(By.ID, "txtTelefonoCitado")
    element.send_keys(context.phone)

    try:
        element = driver.find_element(By.ID, "emailUNO")
        element.send_keys(context.email)

        element = driver.find_element(By.ID, "emailDOS")
        element.send_keys(context.email)
    except Exception:
        pass

    add_reason(driver, context)

    driver.execute_script("enviar();")

    return cita_selection(driver, context)


def confirm_appointment(driver: webdriver, context: CustomerProfile):
    driver.find_element(By.ID, "chkTotal").send_keys(Keys.SPACE)
    driver.find_element(By.ID, "enviarCorreo").send_keys(Keys.SPACE)

    btn = driver.find_element(By.ID, "btnConfirmar")
    btn.send_keys(Keys.ENTER)

    resp_text = body_text(driver)
    ctime = dt.now()

    if "CITA CONFIRMADA Y GRABADA" in resp_text:
        context.bot_result = True
        code = driver.find_element(By.ID, "justificanteFinal").text
        logging.info(f"[Step 6/6] Justificante cita: {code}")
        if context.save_artifacts:
            image_name = f"CONFIRMED-CITA-{ctime}.png".replace(":", "-")
            driver.save_screenshot(image_name)
            # TODO: fix saving to PDF
            # btn = driver.find_element(By.ID, "btnImprimir")
            # btn.send_keys(Keys.ENTER)
            # # Give some time to save appointment pdf
            # time.sleep(5)

        return True
    elif "Lo sentimos, el código introducido no es correcto" in resp_text:
        logging.error("Incorrect code entered")
    else:
        error_name = f"error-{ctime}.png".replace(":", "-")
        driver.save_screenshot(error_name)

    return None


def log_backoff(details):
    logging.error(f"Unable to load the initial page, backing off {details['wait']:0.1f} seconds")


@backoff.on_exception(
    backoff.constant,
    TimeoutException,
    interval=350,
    max_tries=(10 if os.environ.get("CITA_TEST") else None),
    on_backoff=log_backoff,
    logger=None,
)
def initial_page(driver: webdriver, context: CustomerProfile, fast_forward_url, fast_forward_url2):
    if context.first_load:
        driver.delete_all_cookies()

    driver.set_page_load_timeout(300 if context.first_load else 50)
    # Fix chromedriver 103 bug
    time.sleep(1)
    driver.get(fast_forward_url)
    time.sleep(5)
    if context.first_load:
        try:
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
        except Exception as e:
            logging.error(e)
            pass
    driver.get(fast_forward_url2)
    time.sleep(5)

    resp_text = body_text(driver)
    if "INTERNET CITA PREVIA" not in resp_text:
        context.first_load = True
        raise TimeoutException

    context.first_load = False


def cycle_cita(driver: webdriver, context: CustomerProfile, fast_forward_url, fast_forward_url2):
    initial_page(driver, context, fast_forward_url, fast_forward_url2)

    # 1. Instructions page:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "btnEntrar")))
    except TimeoutException:
        logging.error("Timed out waiting for Instructions page to load")
        return None

    if os.environ.get("CITA_TEST") and context.operation_code == OperationType.TOMA_HUELLAS:
        logging.info("Instructions page loaded")
        return True

    driver.find_element(By.ID, "btnEntrar").send_keys(Keys.ENTER)

    # 2. Personal info:
    logging.info("[Step 1/6] Personal info")
    success = False
    if context.operation_code == OperationType.TOMA_HUELLAS:
        success = toma_huellas_step2(driver, context)
    elif context.operation_code == OperationType.RECOGIDA_DE_TARJETA:
        success = recogida_de_tarjeta_step2(driver, context)
    elif context.operation_code == OperationType.SOLICITUD_ASILO:
        success = solicitud_asilo_step2(driver, context)
    elif context.operation_code == OperationType.BREXIT:
        success = brexit_step2(driver, context)
    elif context.operation_code == OperationType.CARTA_INVITACION:
        success = carta_invitacion_step2(driver, context)
    elif context.operation_code in [
        OperationType.CERTIFICADOS_NIE,
        OperationType.CERTIFICADOS_NIE_NO_COMUN,
        OperationType.CERTIFICADOS_RESIDENCIA,
        OperationType.CERTIFICADOS_UE,
    ]:
        success = certificados_step2(driver, context)
    elif context.operation_code == OperationType.AUTORIZACION_DE_REGRESO:
        success = autorizacion_de_regreso_step2(driver, context)
    elif context.operation_code == OperationType.ASIGNACION_NIE:
        success = asignacion_nie_step2(driver, context)

    if not success:
        return None

    time.sleep(2)
    driver.find_element(By.ID, "btnEnviar").send_keys(Keys.ENTER)

    try:
        WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.ID, "btnConsultar")))
    except TimeoutException:
        logging.error("Timed out waiting for Solicitar page to load")

    try:
        wait_exact_time(driver, context)
    except TimeoutException:
        logging.error("Timed out waiting for exact time")
        return None

    # 3. Solicitar cita:
    selection_result = office_selection(driver, context)
    if selection_result is None:
        return None

    # 4. Contact info:
    return phone_mail(driver, context)


# 5. Cita selection
def cita_selection(driver: webdriver, context: CustomerProfile):
    resp_text = body_text(driver)

    if "DISPONE DE 5 MINUTOS" in resp_text:
        logging.info("[Step 4/6] Cita attempt -> selection hit!")
        if context.save_artifacts:
            driver.save_screenshot(f"citas-{dt.now()}.png".replace(":", "-"))

        position = find_best_date_slots(driver, context)
        if not position:
            return None

        time.sleep(2)
        success = process_captcha(driver, context)
        if not success:
            return None

        try:
            driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][name='rdbCita']")[
                position - 1
            ].send_keys(Keys.SPACE)
        except Exception as e:
            logging.error(e)
            pass

        driver.execute_script("envia();")
        time.sleep(0.5)
        driver.switch_to.alert.accept()
    elif "Seleccione una de las siguientes citas disponibles" in resp_text:
        logging.info("[Step 4/6] Cita attempt -> selection hit!")
        if context.save_artifacts:
            driver.save_screenshot(f"citas-{dt.now()}.png".replace(":", "-"))

        try:
            date_els = driver.find_elements(
                By.CSS_SELECTOR, "#CitaMAP_HORAS thead [class^=colFecha]"
            )
            dates = sorted([*map(lambda x: x.text, date_els)])
            slots: Dict[str, list] = {}
            slot_table = driver.find_element(By.CSS_SELECTOR, "#CitaMAP_HORAS tbody")
            for row in slot_table.find_elements(By.CSS_SELECTOR, "tr"):
                appt_time = row.find_elements(By.TAG_NAME, "th")[0].text
                if context.min_time:
                    if appt_time < context.min_time:
                        continue
                if context.max_time:
                    if appt_time > context.max_time:
                        break

                for idx, cell in enumerate(row.find_elements(By.TAG_NAME, "td")):
                    try:
                        if slots.get(dates[idx]):
                            continue
                        slot = cell.find_element(By.CSS_SELECTOR, "[id^=HUECO]").get_attribute(
                            "id"
                        )
                        slots[dates[idx]] = [slot]
                    except Exception:
                        pass

            best_date = find_best_date(sorted(slots), context)
            if not best_date:
                return None
            slot = slots[best_date][0]

            time.sleep(2)
            success = process_captcha(driver, context)
            if not success:
                return None

            driver.execute_script(f"confirmarHueco({{id: '{slot}'}}, {slot[5:]});")
            driver.switch_to.alert.accept()
        except Exception as e:
            logging.error(e)
            return None
    else:
        logging.info("[Step 4/6] Cita attempt -> missed selection")
        return None

    # 6. Confirmation
    resp_text = body_text(driver)

    if "Debe confirmar los datos de la cita asignada" in resp_text:
        logging.info("[Step 5/6] Cita attempt -> confirmation hit!")
        if context.current_solver == recaptchaV3Proxyless:
            context.recaptcha_solver.report_correct_recaptcha()

        try:
            sms_verification = driver.find_element(By.ID, "txtCodigoVerificacion")
        except Exception as e:
            logging.error(e)
            sms_verification = None
            pass

        if context.sms_webhook_token:
            if sms_verification:
                code = get_code(context)
                if code:
                    logging.info(f"Received code: {code}")
                    sms_verification = driver.find_element(By.ID, "txtCodigoVerificacion")
                    sms_verification.send_keys(code)

            confirm_appointment(driver, context)

            if context.save_artifacts:
                driver.save_screenshot(f"FINAL-SCREEN-{dt.now()}.png".replace(":", "-"))

            if context.bot_result:
                driver.quit()
                os._exit(0)
            return None
        else:
            if not sms_verification:
                confirm_appointment(driver, context)

            speaker.say("ENTER THE SHORT CODE FROM SMS")

            logging.info("Press Any button to CLOSE browser")
            input()
            driver.quit()
            os._exit(0)

    else:
        logging.info("[Step 5/6] Cita attempt -> missed confirmation")
        if context.current_solver == recaptchaV3Proxyless:
            context.recaptcha_solver.report_incorrect_recaptcha()
        elif context.current_solver == imagecaptcha:
            context.image_captcha_solver.report_incorrect_image_captcha()

        if context.save_artifacts:
            driver.save_screenshot(f"failed-confirmation-{dt.now()}.png".replace(":", "-"))
        return None


def get_messages(sms_webhook_token):
    try:
        url = f"https://webhook.site/token/{sms_webhook_token}/requests?page=1&sorting=newest"
        return requests.get(url).json()["data"]
    except JSONDecodeError:
        raise Exception("sms_webhook_token is incorrect")


def delete_message(sms_webhook_token, message_id=""):
    url = f"https://webhook.site/token/{sms_webhook_token}/request/{message_id}"
    requests.delete(url)


def get_code(context: CustomerProfile):
    for i in range(60):
        messages = get_messages(context.sms_webhook_token)
        if not messages:
            time.sleep(5)
            continue

        content = messages[0].get("text_content")
        match = re.search("CODIGO (.*), DE", content)
        if match:
            delete_message(context.sms_webhook_token, messages[0].get("uuid"))
            return match.group(1)

    return None


def add_reason(driver: webdriver, context: CustomerProfile):
    try:
        if context.operation_code == OperationType.SOLICITUD_ASILO:
            element = driver.find_element(By.ID, "txtObservaciones")
            element.send_keys(context.reason_or_type)
    except Exception as e:
        logging.error(e)
