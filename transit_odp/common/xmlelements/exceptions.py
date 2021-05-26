class XMLElementException(Exception):
    pass


class XMLAttributeError(XMLElementException):
    pass


class NoElement(XMLElementException):
    pass


class TooManyElements(XMLElementException):
    pass


class ParentDoesNotExist(XMLElementException):
    pass
