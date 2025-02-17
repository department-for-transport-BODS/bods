from typing import Final

from django.utils.translation import gettext as _
from django_hosts import reverse

from config.hosts import ROOT_HOST
from transit_odp.pipelines.models import DatasetETLTaskResult

support_url = reverse("contact", host=ROOT_HOST)
DATA_QUALITY_LABEL: Final = _(
    "I have reviewed the data quality report and wish to publish my data"
)
DATA_QUALITY_WITH_VIOLATIONS_LABEL: Final = _(
    "I acknowledge my data does not meet the standard required, as detailed in the "
    "validation report, and I am publishing non-compliant data to the Bus Open Data "
    "Service."
)

ERROR_CODE_LOOKUP = {
    DatasetETLTaskResult.SYSTEM_ERROR: {
        "description": "Something went wrong and we could not process your "
        "data set. Please try again later."
    },
    DatasetETLTaskResult.FILE_TOO_LARGE: {
        "description": "The file must not exceed 5GB in size"
    },
    DatasetETLTaskResult.ZIP_TOO_LARGE: {
        "description": "The extracted zip file must not exceed 5GB in size"
    },
    DatasetETLTaskResult.NESTED_ZIP_FORBIDDEN: {
        "description": "The zip file must not contain additional zip files"
    },
    DatasetETLTaskResult.NO_DATA_FOUND: {
        "description": "No data was found in the zip file"
    },
    DatasetETLTaskResult.XML_SYNTAX_ERROR: {
        "description": "The dataset contained an XML file which couldn't " "be parsed"
    },
    DatasetETLTaskResult.DANGEROUS_XML_ERROR: {
        "description": "The XML contained prohibited constructs that are "
        "potentially dangerous"
    },
    DatasetETLTaskResult.SCHEMA_VERSION_MISSING: {
        "description": (
            "Missing schema version. Document must define a valid"
            "SchemaVersion attribute. Valid values = 2.1 or 2.4."
        )
    },
    DatasetETLTaskResult.SCHEMA_VERSION_NOT_SUPPORTED: {
        "description": "Schema version not supported. Document must define a "
        "valid SchemaVersion attribute of 2.1 or 2.4."
    },
    DatasetETLTaskResult.SCHEMA_ERROR: {
        "description": "The dataset contained an XML file not compliant with "
        "the TransXChange schema"
    },
    DatasetETLTaskResult.POST_SCHEMA_ERROR: {
        "description": "The dataset contained an XML file not compliant with "
        "post schema checks."
    },
    DatasetETLTaskResult.DATASET_EXPIRED: {
        "description": "The data set has already expired"
    },
    DatasetETLTaskResult.SUSPICIOUS_FILE: {
        "description": "The data published is not suitable according to anti virus checks."
    },
    DatasetETLTaskResult.ANTIVIRUS_FAILURE: {
        "description": "The anti virus checks failed to validate the file(s). Please try again later."
    },
    DatasetETLTaskResult.AV_CONNECTION_ERROR: {
        "description": "The anti virus checks failed to validate the file(s). Please try again later."
    },
}

ERROR_TYPE_PII = "Your TransXchange contains personal identifiable information"
NEXT_STEPS_PII = "Please download the new transXchange tool here"
LINK_PII = "https://www.gov.uk/guidance/publish-bus-open-data#publishing-your-bus-data"
ADDITIONAL_SERVICES_PII = "The Help Desk can be contacted by telephone or email as follows.\n\nTelephone: +44 (0) 800 028 0930\nEmail: bodshelpdesk@kpmg.co.uk"

ERROR_TYPE_SERVICE_CHECK = (
    "Attempted to publish for a service that is already in an active dataset"
)
NEXT_STEPS_SERVICE_CHECK = "Click the supplied link to update your dataset"
