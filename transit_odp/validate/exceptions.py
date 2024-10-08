class ValidationException(Exception):
    code = "VALIDATION_FAILED"
    message_template = "Validation failed for {filename}."

    def __init__(self, filename, line=1, message=None):
        self.filename = filename
        if message is None:
            self.message = self.message_template.format(filename=filename)
        else:
            self.message = message
        self.line = line
