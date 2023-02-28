import pathlib
import unittest

from sgex.call.package import Package
from sgex.call.type import Freqs
from sgex.config import default
from sgex.io import export_content


class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_export = pathlib.Path("sgex/test/tmp/tmp-c82kd8s0")
        cls.url_no_format = "http://localhost:10070/bonito/run.cgi/freqs?format="
        pathlib.Path("sgex/test/tmp").mkdir(exist_ok=True)

    def test_export_content_xlsx(self):
        call = Freqs(
            {
                "format": "xlsx",
                "q": 'alemma,"day"',
                "corpname": "susanne",
                "fcrit": "doc 0",
            }
        )
        p = Package(call, "noske", default)
        p.send_requests()
        export_content(p.responses[0], self.tmp_export)
        self.assertTrue(self.tmp_export.with_suffix(".xlsx").exists())
        self.tmp_export.with_suffix(".xlsx").unlink()
