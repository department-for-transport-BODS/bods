from enum import Enum


class TaskResultsStatus(Enum):
    PENDING = "PENDING"


class ReportStatus(Enum):
    PIPELINE_PENDING = "PIPELINE_PENDING"


CHECKS_DATA = [
    {
        "observation": "Incorrect NOC",
        "importance": "Critical",
        "category": "Data set",
        "queue_name": "incorrect-noc-queue",
    },
    {
        "observation": "First stop is set down only",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "first-stop-is-set-down-only-queue",
    },
    {
        "observation": "Last stop is pick up only",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "last-stop-is-pickup-only-queue",
    },
    {
        "observation": "First stop is not a timing point",
        "importance": "Critical",
        "category": "Timing",
        "queue_name": "first-stop-is-not-a-timing-point-queue",
    },
    {
        "observation": "Last stop is not a timing point",
        "importance": "Critical",
        "category": "Timing",
        "queue_name": "last-stop-is-not-a-timing-point-queue",
    },
    {
        "observation": "Incorrect stop type",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "incorrect-stop-type-queue",
    },
    {
        "observation": "Missing journey code",
        "importance": "Critical",
        "category": "Journey",
        "queue_name": "missing-journey-code-queue",
    },
    {
        "observation": "Duplicate journey code",
        "importance": "Critical",
        "category": "Journey",
        "queue_name": "duplicate-journey-code-queue",
    },
    {
        "observation": "Missing bus working number",
        "importance": "Advisory",
        "category": "Journey",
        "queue_name": "missing-bus-working-number-queue",
    },
    {
        "observation": "Missing stop",
        "importance": "Advisory",
        "category": "Stop",
        "queue_name": "missing-stop-queue",
    },
    {
        "observation": "Stop not found in NaPTAN",
        "importance": "Critical",
        "category": "Stop",
        "queue_name": "stop-not-found-in-naptan-queue",
    },
    {
        "observation": "Same stop found multiple times",
        "importance": "Advisory",
        "category": "Stop",
        "queue_name": "same-stop-found-multiple-times-queue",
    },
    {
        "observation": "Incorrect licence number",
        "importance": "Critical",
        "category": "Data set",
        "queue_name": "incorrect-licence-number-queue",
    },
]


class Checks(Enum):
    IncorrectNoc = "Incorrect NOC"
    FirstStopIsSetDown = "First stop is set down only"
    LastStopIsPickUpOnly = "Last stop is pick up only"
    IncorrectStopType = "Incorrect stop type"
    StopNotFoundInNaptan = "Stop not found in NaPTAN"
