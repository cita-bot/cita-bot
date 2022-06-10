import logging
import os
import unittest

from bcncita import (
    CustomerProfile,
    DocType,
    Office,
    OperationType,
    Province,
    init_wedriver,
    start_with,
    try_cita,
)


class TestBot(unittest.TestCase):
    def test_cita(self):
        params = {
            "chrome_driver_path": "chromedriver",
            "auto_office": True,
            "auto_captcha": True,
            "name": "BORIS JOHNSON",
            "doc_type": DocType.PASSPORT,
            "doc_value": "132435465",
            "phone": "600000000",
            "email": "ghtvgdr@affecting.org",
        }

        customer = CustomerProfile(
            **params,
            province=Province.BARCELONA,
            operation_code=OperationType.BREXIT,
            offices=[Office.BARCELONA],
        )
        with self.assertLogs(None, level=logging.INFO) as logs:
            try_cita(context=customer, cycles=1)

        self.assertIn("INFO:root:\x1b[33m[Attempt 1/1]\x1b[0m", logs.output)
        self.assertIn("INFO:root:[Step 1/6] Personal info", logs.output)
        self.assertIn("INFO:root:[Step 2/6] Office selection", logs.output)
        self.assertIn("INFO:root:[Step 3/6] Contact info", logs.output)
        self.assertIn("INFO:root:[Step 4/6] Cita attempt -> selection hit!", logs.output)

        driver = init_wedriver(customer)
        for province in Province:
            customer = CustomerProfile(
                **params,
                province=province,
                operation_code=OperationType.TOMA_HUELLAS,
            )
            with self.assertLogs(None, level=logging.INFO) as logs:
                start_with(driver=driver, context=customer, cycles=1)

            self.assertIn(
                "INFO:root:Instructions page loaded",
                logs.output,
                msg=f"Can't load instructions for province={province}",
            )


if __name__ == "__main__":
    if not os.environ.get("CITA_TEST"):
        os._exit(0)
    unittest.main()
