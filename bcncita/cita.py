import datetime
import json
import logging
import os
import random
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from telegram.ext import CommandHandler, Updater

from .speaker import new_speaker

__all__ = ["try_cita", "CustomerProfile", "DocType", "OperationType", "Office"]


CAPTCHA_TIMEOUT = 300

CYCLES = 144
REFRESH_PAGE_CYCLES = 12

DELAY = 30  # timeout for page load

speaker = new_speaker()


class DocType(str, Enum):
    PASSPORT = "passport"
    NIE = "nie"


class OperationType(str, Enum):
    TOMA_HUELLAS = "4010"  # POLICIA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) Y RENOVACIÓN DE TARJETA DE LARGA DURACIÓN
    RECOGIDA_DE_TARJETA = "4036"  # POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)
    SOLICITUD = "4"  # EXTRANJERIA - SOLICITUD DE AUTORIZACIONES
    BREXIT = "4094"  # POLICÍA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA CIUDADANOS BRITÁNICOS Y SUS FAMILIARES (BREXIT)


class Office(str, Enum):
    BADALONA = "18"  # CNP-COMISARIA BADALONA, AVDA. DELS VENTS (9)
    BARCELONA = "16"  # CNP - RAMBLA GUIPUSCOA 74, RAMBLA GUIPUSCOA (74)
    BARCELONA_MALLORCA = "14"  # CNP MALLORCA-GRANADOS, MALLORCA (213)
    CERDANYOLA = "20"  # CNP-COMISARIA CERDANYOLA DEL VALLES, VERGE DE LES FEIXES (4)
    GRANOLLERS = "28"  # CNP-COMISARIA GRANOLLERS, RICOMA (65)
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
    VILANOVA = "39"  # CNP-COMISARIA VILANOVA I LA GELTRU, VAPOR (19)


@dataclass
class CustomerProfile:
    name: str
    doc_type: DocType
    doc_value: str  # Passport? "123123123"; Nie? "Y1111111M"
    phone: str
    email: str
    city: str = "Barcelona"
    operation_code: OperationType = OperationType.TOMA_HUELLAS
    country: str = "RUSIA"
    year_of_birth: Optional[str] = None
    card_expire_date: Optional[str] = None  # "dd/mm/yyyy"
    offices: Optional[list] = field(default_factory=list)

    anticaptcha_api_key: Optional[str] = None
    anticaptcha_plugin_path: Optional[str] = None
    auto_captcha: bool = True
    auto_office: bool = True
    chrome_driver_path: str = "/usr/local/bin/chromedriver"
    chrome_profile_name: Optional[str] = None
    chrome_profile_path: Optional[str] = None
    fast_forward_url: Optional[str] = None
    save_artifacts: bool = False
    telegram_token: Optional[str] = None
    wait_exact_time: Optional[list] = None  # [[minute, second]]

    # Internals
    bot_result: bool = False
    first_load: Optional[bool] = True  # Wait more on the first load to cache stuff
    log_settings: Optional[dict] = field(default_factory=lambda: {"stream": sys.stdout})
    updater: Any = object()


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
        # precisely we send a standard window.postMessage method
        return driver.execute_script(
            """
        return window.postMessage({});
        """.format(
                json.dumps(message)
            )
        )

    browser = init_chrome(context)

    # https://anti-captcha.com/clients/settings/apisetup
    if context.auto_captcha:
        browser.get("https://antcpt.com/blank.html")
        acp_api_send_request(
            browser, "setOptions", {"options": {"antiCaptchaApiKey": context.anticaptcha_api_key}}
        )
        time.sleep(1)

    return browser


def init_chrome(context: CustomerProfile):
    options = webdriver.ChromeOptions()

    if context.chrome_profile_path:
        options.add_argument(f"user-data-dir={context.chrome_profile_path}")
    if context.chrome_profile_name:
        options.add_argument(f"profile-directory={context.chrome_profile_name}")
    if context.auto_captcha:
        options.add_extension(context.anticaptcha_plugin_path)

    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

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
    logging.basicConfig(
        format="%(asctime)s - %(message)s", level=logging.INFO, **context.log_settings
    )
    if context.telegram_token:
        context.updater = Updater(token=context.telegram_token, use_context=True)
    success = False
    result = False
    for i in range(cycles):
        try:
            result = cycle_cita(driver, context)
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
    # 4. Data form:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtFecha")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select country
    select = Select(driver.find_element_by_id("txtPaisNac"))
    select.select_by_visible_text(context.country)

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element_by_id("rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element_by_id("rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element_by_id("txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    if context.card_expire_date:
        element = driver.find_element_by_id("txtFecha")
        element.send_keys(context.card_expire_date)

    success = process_captcha(driver, context)
    if not success:
        return

    return True


def recogida_de_tarjeta_step2(driver: webdriver, context: CustomerProfile):
    # 4. Data form:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element_by_id("rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element_by_id("rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element_by_id("txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    success = process_captcha(driver, context)
    if not success:
        return

    return True


def solicitud_step2(driver: webdriver, context: CustomerProfile):
    # Data form:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element_by_id("rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element_by_id("rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element_by_id("txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name, Keys.TAB, context.year_of_birth)

    success = process_captcha(driver, context)
    if not success:
        return

    return True


def brexit_step2(driver: webdriver, context: CustomerProfile):
    # 4. Data form:
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return None

    # Select doc type
    if context.doc_type == DocType.PASSPORT:
        driver.find_element_by_id("rdbTipoDocPas").send_keys(Keys.SPACE)
    elif context.doc_type == DocType.NIE:
        driver.find_element_by_id("rdbTipoDocNie").send_keys(Keys.SPACE)

    # Enter doc number and name
    element = driver.find_element_by_id("txtIdCitado")
    element.send_keys(context.doc_value, Keys.TAB, context.name)

    success = process_captcha(driver, context)
    if not success:
        return

    return True


def wait_exact_time(driver: webdriver, context: CustomerProfile):
    if context.wait_exact_time:
        WebDriverWait(driver, 1200).until(
            lambda _x: [datetime.datetime.now().minute, datetime.datetime.now().second]
            in context.wait_exact_time
        )


def body_text(driver: webdriver):
    try:
        WebDriverWait(driver, DELAY).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return driver.find_element_by_tag_name("body").text
    except TimeoutException:
        logging.info("Timed out waiting for body to load")
        return ""


def process_captcha(driver: webdriver, context: CustomerProfile, partially: bool = False):
    for i in range(1, 4):
        if context.auto_captcha:
            # wait for captcha and proceed:
            WebDriverWait(driver, CAPTCHA_TIMEOUT).until(
                lambda x: x.find_element_by_css_selector(".antigate_solver.solved")
            )
        else:
            logging.info("HEY, FIX CAPTCHA and press ENTER")
            input()
            logging.info("OK, Waiting")

        # stop the function upon captcha is solved
        if partially:
            return True

        time.sleep(0.3)
        btn = driver.find_element_by_id("btnEnviar")
        btn.send_keys(Keys.ENTER)

        time.sleep(0.3)
        try:
            WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.ID, "btnConsultar")))
            break
        except TimeoutException:
            logging.error("Captcha loop")

        if i == 3:
            # Failed to get captcha
            logging.error("Tries exceeded")
            return None

    return True


def select_office(driver: webdriver, context: CustomerProfile):
    if not context.auto_office:
        speaker.say("MAKE A CHOICE")
        logging.info("Press Any Key")
        input()
        return True
    else:
        el = driver.find_element_by_id("idSede")
        select = Select(el)
        if context.save_artifacts:
            offices_path = os.path.join(
                os.getcwd(), f"offices-{datetime.datetime.now()}.html".replace(":", "-")
            )
            with open(offices_path, "w") as f:
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
                    pass

            select.select_by_index(random.randint(0, len(select.options) - 1))
            return True


def solicitar_cita(driver: webdriver, context: CustomerProfile):
    driver.execute_script("enviar('solicitud');")

    for i in range(REFRESH_PAGE_CYCLES):
        resp_text = body_text(driver)

        if "Por favor, valide el Captcha para poder continuar" in resp_text:
            success = process_captcha(driver, context, partially=True)
            if not success:
                return None

            return solicitar_cita(driver, context)

        elif "Seleccione la oficina donde solicitar la cita" in resp_text:
            logging.info("Towns hit! :)")

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

            btn = driver.find_element_by_id("btnSiguiente")
            btn.send_keys(Keys.ENTER)
            return True
        elif "En este momento no hay citas disponibles" in resp_text:
            time.sleep(5)
            driver.refresh()
            continue
        else:
            logging.info("No towns")
            return None


def phone_mail(driver: webdriver, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(EC.presence_of_element_located((By.ID, "emailDOS")))
        logging.info("Email page hit")
    except TimeoutException:
        logging.error("Timed out waiting for phone/email to load")
        return None

    element = driver.find_element_by_id("txtTelefonoCitado")
    element.clear()
    element.send_keys(context.phone)  # phone num

    element = driver.find_element_by_id("emailUNO")
    element.clear()
    element.send_keys(context.email)

    element = driver.find_element_by_id("emailDOS")
    element.clear()
    element.send_keys(context.email)

    driver.execute_script("enviar();")

    return cita_selection(driver, context)


def cycle_cita(driver: webdriver, context: CustomerProfile):
    driver.delete_all_cookies()
    try:
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
    except Exception as e:
        logging.error(e)
        pass

    if context.fast_forward_url:
        while True:
            try:
                driver.set_page_load_timeout(300 if context.first_load else 50)
                driver.get(context.fast_forward_url)
            except TimeoutException:
                logging.error("Timed out loading initial page")
                continue
            break
        context.first_load = False
        session_id = driver.get_cookie("JSESSIONID").get("value")
        logging.info(session_id)
    else:
        driver.get("https://sede.administracionespublicas.gob.es/icpplus/index.html")
        time.sleep(1)  # Let the user actually see something!

        # Select "Barcelona"
        select = Select(driver.find_element_by_id("form"))
        select.select_by_visible_text(context.city)

        btn = driver.find_element_by_id("btnAceptar")
        btn.send_keys(Keys.ENTER)

        # 2. Tramite selection:
        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "tramiteGrupo[1]"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for tramite to load")
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
        logging.error("Timed out waiting for Instructions page to load")
        return None

    btn = driver.find_element_by_id("btnEntrar")
    btn.send_keys(Keys.ENTER)

    # 4. Data form:
    success = False
    if context.operation_code == OperationType.TOMA_HUELLAS:
        success = toma_huellas_step2(driver, context)
    elif context.operation_code == OperationType.RECOGIDA_DE_TARJETA:
        success = recogida_de_tarjeta_step2(driver, context)
    elif context.operation_code == OperationType.SOLICITUD:
        success = solicitud_step2(driver, context)
    elif context.operation_code == OperationType.BREXIT:
        success = brexit_step2(driver, context)

    if not success:
        return None

    try:
        wait_exact_time(driver, context)
    except TimeoutException:
        logging.error("Timed out waiting for exact time")
        return None

    # 5. Solicitar cita:
    solcitar = solicitar_cita(driver, context)
    if solcitar is None:
        return None

    # 6. phone-mail:
    return phone_mail(driver, context)


# 7. Cita selection
def cita_selection(driver: webdriver, context: CustomerProfile):
    resp_text = body_text(driver)

    if "Por favor, valide el Captcha para poder continuar" in resp_text:
        success = process_captcha(driver, context, partially=True)
        if not success:
            return None

        return phone_mail(driver, context)

    elif "DISPONE DE 5 MINUTOS" in resp_text:
        logging.info("Cita attempt -> selection hit! :)")
        if context.save_artifacts:
            driver.save_screenshot(f"citas-{datetime.datetime.now()}.png".replace(":", "-"))

        try:
            driver.find_elements_by_css_selector("input[type='radio'][name='rdbCita']")[
                0
            ].send_keys(Keys.SPACE)
        except Exception as e:
            logging.error(e)
            pass

        btn = driver.find_element_by_id("btnSiguiente")
        btn.send_keys(Keys.ENTER)
        driver.switch_to.alert.accept()
    else:
        logging.info("Cita attempt -> missed selection :(")
        return None

    # 8. Confirmation
    resp_text = body_text(driver)

    if "Debe confirmar los datos de la cita asignada" in resp_text:
        logging.info("Cita attempt -> confirmation hit! :)")

        if context.telegram_token:
            dispatcher = context.updater.dispatcher

            def shutdown():
                context.updater.stop()
                context.updater.is_idle = False

            def code_received(update, ctx):
                logging.info(f"Received code: {ctx.args[0]}")

                element = driver.find_element_by_id("txtCodigoVerificacion")
                element.send_keys(ctx.args[0])

                driver.find_element_by_id("chkTotal").send_keys(Keys.SPACE)
                driver.find_element_by_id("enviarCorreo").send_keys(Keys.SPACE)

                btn = driver.find_element_by_id("btnConfirmar")
                btn.send_keys(Keys.ENTER)

                resp_text = body_text(driver)
                ctime = datetime.datetime.now()

                if "CITA CONFIRMADA Y GRABADA" in resp_text:
                    context.bot_result = True
                    code = driver.find_element_by_id("justificanteFinal").text
                    logging.info(f"Justificante cita: {code}")
                    caption = f"Cita confirmed! {code}"
                    if context.save_artifacts:
                        image_name = f"CONFIRMED-CITA-{ctime}.png".replace(":", "-")
                        driver.save_screenshot(image_name)
                        ctx.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=open(os.path.join(os.getcwd(), image_name), "rb"),
                            caption=caption,
                        )
                        btn = driver.find_element_by_id("btnImprimir")
                        btn.send_keys(Keys.ENTER)
                    else:
                        ctx.bot.send_message(chat_id=update.effective_chat.id, text=caption)

                    threading.Thread(target=shutdown).start()
                    return True
                elif "Lo sentimos, el código introducido no es correcto" in resp_text:
                    ctx.bot.send_message(
                        chat_id=update.effective_chat.id, text="Incorrect, please try again"
                    )
                else:
                    error_name = f"error-{ctime}.png".replace(":", "-")
                    driver.save_screenshot(error_name)
                    ctx.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=open(os.path.join(os.getcwd(), error_name), "rb"),
                    )
                    ctx.bot.send_message(
                        chat_id=update.effective_chat.id, text="Something went wrong"
                    )

            dispatcher.add_handler(CommandHandler("code", code_received, pass_args=True))
            context.updater.start_polling(poll_interval=1.0)

            for i in range(5):
                speaker.say("ALARM")
            # Waiting for response 5 minutes
            time.sleep(360)
            threading.Thread(target=shutdown).start()
            if context.save_artifacts:
                driver.save_screenshot(
                    f"FINAL-SCREEN-{datetime.datetime.now()}.png".replace(":", "-")
                )

            if context.bot_result:
                driver.quit()
                os._exit(0)
            return None
        else:
            for i in range(10):
                speaker.say("ALARM")
            logging.info("Press Any button to CLOSE browser")
            input()
            driver.quit()
            os._exit(0)

    else:
        logging.info("Cita attempt -> missed confirmation :(")
        if context.save_artifacts:
            driver.save_screenshot(
                f"failed-confirmation-{datetime.datetime.now()}.png".replace(":", "-")
            )
        return None
