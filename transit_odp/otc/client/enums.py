from enum import Enum


class RegistrationStatusEnum(Enum):
    ADMIN_CANCELLED = "Admin Cancelled"
    CANCELLED = "Cancelled"
    NEW = "New"
    REFUSED = "Refused"
    SURRENDERED = "Surrendered"
    REVOKED = "Revoked"
    CNS = "CNS"
    CANCELLATION = "Cancellation"
    EXPIRED = "Expired"
    WITHDRAWN = "Withdrawn"
    VARIATION = "Variation"
    REGISTERED = "Registered"

    @classmethod
    def to_delete(cls):
        return [
            cls.ADMIN_CANCELLED.value,
            cls.CANCELLED.value,
            cls.NEW.value,
            cls.REFUSED.value,
            cls.SURRENDERED.value,
            cls.REVOKED.value,
            cls.CNS.value,
        ]

    @classmethod
    def to_change(cls):
        return [
            cls.CANCELLATION.value,
            cls.EXPIRED.value,
            cls.WITHDRAWN.value,
            cls.VARIATION.value,
        ]


class TaskResultStatus(Enum):
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
