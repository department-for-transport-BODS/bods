from io import BytesIO, StringIO
from pathlib import Path

from transit_odp.data_quality.pti.tests.constants import TXC_END, TXC_START

DATA_DIR = Path(__file__).parent / "data"


class XMLFile(BytesIO):
    def __init__(self, str_, **kwargs):
        super().__init__(**kwargs)
        self.write(str_.encode("utf-8"))
        self.name = "file.xml"
        self.seek(0)


class TXCFile(XMLFile):
    def __init__(self, str_, **kwargs):
        s = TXC_START + str_ + TXC_END
        super().__init__(s, **kwargs)
        self.name = "txc.xml"


class JSONFile(StringIO):
    def __init__(self, str_, **kwargs):
        super().__init__(**kwargs)
        self.write(str_)
        self.seek(0)
        self.name = "pti_schema.json"
