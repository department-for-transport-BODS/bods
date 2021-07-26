TXC_BASE_URL = (
    "http://www.transxchange.org.uk/schema/{version}/TransXChange_general.xsd"
)
TXC_21 = "2.1"
TXC_24 = "2.4"
TWO_ONE_URL = TXC_BASE_URL.format(version=TXC_21)
TWO_FOUR_URL = TXC_BASE_URL.format(version=TXC_24)
TXC_MAP = {TXC_21: TWO_ONE_URL, TXC_24: TWO_FOUR_URL}

TRANSXCAHNGE_NAMESPACE = "http://www.transxchange.org.uk/"
TRANSXCHANGE_NAMESPACE_PREFIX = "x"

PTI_COMMENT = "PTI validation report and Updated DQ score"
