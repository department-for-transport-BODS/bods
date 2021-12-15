from datetime import datetime, timezone
from time import time_ns

from factory import Factory, LazyFunction, SubFactory

from transit_odp.avl.validation.models import (
    Error,
    Header,
    Identifier,
    Observation,
    Result,
    SchemaError,
    SchemaValidationResponse,
    ValidationResponse,
    ValidationSummary,
)


class ObservationFactory(Factory):
    """
    A BODS Observation.

    Args:
        details: Details of the observation.
        category: The observations category.
        reference: A reference to guidance for this observation.
        context: An XPath query for the element that the tests are applied to.
        number: The unique identifier for the observation.
    """

    details = "An observation detail"
    category = "Critical"
    reference = "Reference for an observation"
    context = "//x:VehicleActivity"
    number = 1

    class Meta:
        model = Observation


class HeaderFactory(Factory):
    """
    A result header.

    Args:
        packet_name: The filename of the packet.
        timestamp: The timestamp of the packet.
        feed_id: The feed id of the packet.
        plugin: The plugin that recorded the packet.
    """

    packet_name = "avl-internal-1000000"
    timestamp = LazyFunction(time_ns)
    feed_id = 1
    plugin = "avl-internal"

    class Meta:
        model = Header


class IdentifierFactory(Factory):
    """
    A class for identifying a SIRI VM element.

    Args:
        item_identifier: The ItemIdentifier value.
        line_ref: The LineRef value.
        name: The name of the element.
        operator_ref: The OperatorRef value.
        recorded_at_time: The RecordedAtTime.
        vehicle_journey_ref: The VehicleJourneyRef value.
        vehicle_ref: The VehicleRef value.
    """

    item_identifier = "Item1"
    line_ref = "Line1"
    name = "OriginRef"
    operator_ref = "Op1"
    recorded_at_time = LazyFunction(lambda: datetime.now(timezone.utc))
    vehicle_journey_ref = "JVRef1"
    vehicle_ref = "JR1"

    class Meta:
        model = Identifier


class ErrorFactory(Factory):
    """
    A AVL validation error.

    Args:
        level: Whether the error is critical or non-critical.
        context: The packet element that has the issue.
        details: Details of the error.
        identifier: The Identifier object used to identify the element.
    """

    level = "Critical"
    context = "//x:VehicleActivity"
    details = "This is a detail"
    identifier = SubFactory(IdentifierFactory)

    class Meta:
        model = Error


class ResultFactory(Factory):
    """
    The result of a packet analysis.

    Args:
        header: A header describing the packet analysed.
        errors: A list of issues with the packet.
    """

    header = SubFactory(HeaderFactory)
    errors = []

    class Meta:
        model = Result


class ValidationSummaryFactory(Factory):

    """
    A summary of the AVL validation results.

    total_error_count: Total number of errors found for all packets.
    critical_error_count: Total number of critical errors.
    non_critical_error_count: Total number of non-critical errors.
    critical_score: Critical error score.
    non_critical_score: Non-critical error score.
    vehicle_activity_count: Number of vehicle activity elements in all packets.
    """

    total_error_count = 0
    critical_error_count = 0
    non_critical_error_count = 0
    vehicle_activity_count = 5
    critical_score = 1.0
    non_critical_score = 1.0

    class Meta:
        model = ValidationSummary


class ValidationResponseFactory(Factory):
    """
    The response sent from the validation service.

    Args:
        feed_id: The id of the feed analysed.
        packet_count: The total number of packets analysed.
        validation_summary: A summary of the validation.
        results: A list of the results of every packet in the analysis.
    """

    feed_id = 1
    packet_count = 100
    validation_summary = SubFactory(ValidationSummaryFactory)
    results = []

    class Meta:
        model = ValidationResponse


class SchemaErrorFactory(Factory):
    """
    A schema validation error factory.

    Args:
        domain_name: The xml domain name.
        filename: The xml filename.
        level_name: The name of the error level.
        line: The line the error occurs on.
        message: The error message.
        path: The path to the element that has the issue.
        type_name: The type of error.
    """

    domain_name = "SCHEMASV"
    filename = "<string>"
    level_name = "ERROR"
    line = 1
    message = (
        "Element 'Siri': No matching global declaration "
        "available for the validation root."
    )
    path = "/Siri"
    type_name = "SCHEMAV_CVC_ELT_1"

    class Meta:
        model = SchemaError


class SchemaValidationResponseFactory(Factory):
    """
    A schema validation response factory

    Args:
        feed_id: The id of the feed.
        is_valid: True if the packet has no schema issues, False otherwise.
        errors: A list of all the schema validation errors.
    """

    feed_id = 1
    is_valid = True
    timestamp = 1631603094
    errors = []

    class Meta:
        model = SchemaValidationResponse
