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
    DatasetETLTaskResult.DATASET_EXPIRED: {
        "description": "The data set has already expired"
    },
    DatasetETLTaskResult.SUSPICIOUS_FILE: {
        "description": f"Our anti virus scan detected an issue with your data"
        f"set. If you believe this to be "
        f'wrong, please <a class="govuk-link" href="{support_url}">contact '
        f"support</a>."
    },
}
