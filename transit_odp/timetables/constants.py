from django.conf import settings

TXC_21 = "2.1"
TXC_24 = "2.4"

TRANSXCAHNGE_NAMESPACE = "http://www.transxchange.org.uk/"
TRANSXCHANGE_NAMESPACE_PREFIX = "x"

PTI_COMMENT = "PTI validation report and Updated DQ score"


def get_txc_map():
    txc_base_url = settings.TXC_BASE_URL + "/schema/{version}/TransXChange_general.xsd"
    return {
        TXC_21: txc_base_url.format(version=TXC_21),
        TXC_24: settings.TXC_V24_OVERRIDE or txc_base_url.format(version=TXC_24),
    }
