import logging
import unittest

from bcncita import CustomerProfile, DocType, Office, OperationType, Province, try_cita


class TestBot(unittest.TestCase):
    def test_cita(self):
        customer = CustomerProfile(
            chrome_driver_path="chromedriver",
            province=Province.BARCELONA,
            operation_code=OperationType.BREXIT,
            auto_office=True,
            offices=[Office.BARCELONA],
            auto_captcha=True,
            name="BORIS JOHNSON",
            doc_type=DocType.PASSPORT,
            doc_value="132435465",
            phone="600000000",
            email="ghtvgdr@affecting.org",
        )
        with self.assertLogs(None, level=logging.INFO) as logs:
            try_cita(context=customer, cycles=1)

        self.assertIn("INFO:root:\x1b[33m[Attempt 1/1]\x1b[0m", logs.output)
        self.assertIn("INFO:root:[Step 1/6] Personal info", logs.output)
        self.assertIn("INFO:root:[Step 2/6] Office selection", logs.output)
        self.assertIn("INFO:root:[Step 3/6] Contact info", logs.output)
        self.assertIn("INFO:root:[Step 4/6] Cita attempt -> selection hit!", logs.output)


if __name__ == "__main__":
    unittest.main()
