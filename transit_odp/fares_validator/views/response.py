"""
Used for forming responses for validator functions
"""


class XMLViolationDetail():
    def __init__(self, is_violation, violation_line=None, violation_message=None):
        self.is_violation = is_violation
        self.violation_line = str(violation_line)
        self.violation_message = violation_message
        self.violation_detail = []
        if is_violation == "violation":
            self.violation_detail = [self.is_violation, self.violation_line, self.violation_message]
    
    def __list__(self):
        return self.violation_detail






