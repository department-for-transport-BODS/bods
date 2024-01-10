from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Observation(BaseModel):
    """
    A BODS Observation.

    Args:
        details: Details of the observation.
        category: The observations category.
        reference: A reference to guidance for this observation.
        context: An XPath query for the element that the tests are applied to.
        number: The unique identifier for the observation.
        rules: A list of rules to evaluate on the context element.
    """

    details: str
    category: str
    reference: str
    context: str
    number: int


class Header(BaseModel):
    """
    A result header.

    Args:
        packet_name: The filename of the packet.
        timestamp: The timestamp of the packet.
        feed_id: The feed id of the packet.
        plugin: The plugin that recorded the packet.
    """

    packet_name: str
    timestamp: int
    feed_id: int
    plugin: str


class Identifier(BaseModel):
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

    item_identifier: Optional[str] = None
    line_ref: Optional[str] = None
    name: str
    operator_ref: Optional[str] = None
    recorded_at_time: Optional[datetime] = None
    vehicle_journey_ref: Optional[str] = None
    vehicle_ref: Optional[str] = None


class Error(BaseModel):
    """
    A AVL validation error.

    Args:
        level: Whether the error is critical or non-critical.
        context: The packet element that has the issue.
        details: Details of the error.
        identifier: The Identifier object used to identify the element.
    """

    level: str
    context: str
    details: str
    identifier: Identifier


class Result(BaseModel):
    """
    The result of a packet analysis.

    Args:
        header: A header describing the packet analysed.
        errors: A list of issues with the packet.
    """

    header: Header
    errors: List[Error]


class ValidationSummary(BaseModel):

    """
    A summary of the AVL validation results.

    total_error_count: Total number of errors found for all packets.
    critical_error_count: Total number of critical errors.
    non_critical_error_count: Total number of non-critical errors.
    critical_score: Critical error score.
    non_critical_score: Non-critical error score.
    vehicle_activity_count: Number of vehicle activity elements in all packets.
    """

    total_error_count: int
    critical_error_count: int
    non_critical_error_count: int
    vehicle_activity_count: int
    critical_score: float
    non_critical_score: float


class ValidationResponse(BaseModel):
    """
    The response sent from the validation service.

    Args:
        feed_id: The id of the feed analysed.
        packet_count: The total number of packets analysed.
        validation_summary: A summary of the validation.
        results: A list of the results of every packet in the analysis.
    """

    feed_id: int
    packet_count: int
    validation_summary: ValidationSummary
    results: List[Result]


class SchemaError(BaseModel):
    """
    A schema validation error.

    Args:
        domain_name: The xml domain name.
        filename: The xml filename.
        level_name: The name of the error level.
        line: The line the error occurs on.
        message: The error message.
        path: The path to the element that has the issue.
        type_name: The type of error.
    """

    domain_name: str
    filename: str
    level_name: str
    line: int
    message: str
    path: str
    type_name: str


class SchemaValidationResponse(BaseModel):
    """
    A validation response

    Args:
        feed_id: The id of the feed.
        is_valid: True if the packet has no schema issues, False otherwise.
        timestamp: The timestamp of when Real Time processed the packet
        errors: A list of all the schema validation errors.
    """

    feed_id: int
    is_valid: bool
    timestamp: int
    errors: List[SchemaError]
