import json
import logging
from typing import Dict

import pandas as pd

from transit_odp.data_quality.models import DataQualityReport
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.pipelines.dqs_report_etl.config import (
    MODEL_CONFIG,
    WARNING_CONFIG,
)
from transit_odp.pipelines.pipelines.dqs_report_etl.models import (
    ExtractedData,
    ExtractedModel,
    ExtractedWarnings,
)
from transit_odp.pipelines.pipelines.dqs_report_etl.utils import load_geojson

logger = logging.getLogger(__name__)

LOGGER_PREFIX = "[DQS] "


def run(report_id: int) -> ExtractedData:
    _prefix = LOGGER_PREFIX + f"Report {report_id} => "
    logger.info(_prefix + "Beginning DQS extraction.")
    report = get_report(report_id)
    logger.info(_prefix + "Getting report from database.")
    data = get_report_json(report)
    logger.info(_prefix + "Extracting model data from report.")
    model = extract_model(data)
    logger.info(_prefix + "Extracting warnings from report.")
    warnings = extract_warnings(report, data)
    return ExtractedData(report=report, model=model, warnings=warnings)


def get_report(report_id: int):
    try:
        return DataQualityReport.objects.select_related(
            "revision__dataset__organisation"
        ).get(id=report_id)
    except DataQualityReport.DoesNotExist:
        logger.exception(f"DataQualityReport with id={report_id} does not exist")
        raise


def get_report_json(report: DataQualityReport):
    try:
        with report.file.open("r") as fin:
            return json.load(fin)
    except ValueError as e:
        logging.exception("Could not open report file")
        raise PipelineException() from e


def extract_model(data: Dict) -> ExtractedModel:
    """Extract the transmodel/naptan entities referenced by the report"""

    model = {}
    for key, config in MODEL_CONFIG.items():

        # Get DataFrame config
        frame_builder = load_geojson if config["geojson"] else pd.DataFrame
        columns = config["columns"]
        rename_columns = config.get("rename_columns", {})
        index_col = config["index_column"]

        model_data = data["model"].get(key, [])

        if not model_data:
            logger.info(f"No data for model '{key}' found in report.")

        try:
            # Create the DataFrame
            df = frame_builder(model_data, columns=columns)

            # Rename columns
            df = df.rename(columns=rename_columns)

            # Set the DataFrame index
            df = df.set_index(index_col, verify_integrity=True)

        except ValueError as e:
            logger.error(f"Model '{key}' is not valid")
            raise PipelineException(f"Model '{key}' is not valid") from e

        model[key] = df

    return ExtractedModel(**model)


def extract_warnings(report: DataQualityReport, data: Dict) -> ExtractedWarnings:
    "Extract the warnings in the report"

    report_warnings = {
        warning["warning_type"].replace("-", "_"): warning["values"]
        for warning in data["warnings"]
    }

    warnings = {}
    for key, config in WARNING_CONFIG.items():

        warning_data = report_warnings.get(key)

        if not warning_data:
            logger.info(f"No data for warning '{key}' found in report.")

        # Create DataFrame from warnings
        df = pd.DataFrame(warning_data, columns=config["columns"])

        # Rename columns
        rename_columns = config.get("rename_columns", {})
        df = df.rename(columns=rename_columns)

        # Set index
        df = df.set_index("ito_id")

        warnings[key] = df

    return ExtractedWarnings(**warnings)
