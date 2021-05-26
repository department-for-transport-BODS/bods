class TransXChangeException(Exception):
    pass


class MissingLines(TransXChangeException):
    def __init__(self, service):
        self.service = service


class TimetableDoesNotExist(TransXChangeException):
    pass


class TimetableUnavailable(TransXChangeException):
    pass
