BODS_HOST = "https://data.bus-data.dft.gov.uk"
BODS_API_URL = BODS_HOST + "/api"

V1 = BODS_API_URL + "/v1"

V1_TIMETABLES_URL = V1 + "/dataset"
V1_FARES_URL = V1 + "/fares/dataset"
V1_GTFS_RT_URL = V1 + "/gtfsrtdatafeed"
V1_SIRI_VM_URL = V1 + "/datafeed"

TIMETABLES_PATH = "dataset"
FARES_PATH = "fares/dataset"
GTFS_RT_PATH = "gtfsrtdatafeed"
SIRI_VM_PATH = "datafeed"

V2 = BODS_API_URL + "/v2"

OPERATORS_PATH = "operators"
V2_TIMETABLES_PATH = "timetables"
TXC_FILES_PATH = "txcfiles"
AVL_FEEDS_PATH = "avlfeeds"

DATASET_STATUSES = ["published", "error", "expired", "inactive"]

OK_200 = 200
NOT_FOUND_404 = 404
