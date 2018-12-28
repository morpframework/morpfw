
class UnprocessableError(Exception):
    def __init__(self, message=None):
        self.message = message or ''


class ValidationError(Exception):
    def __init__(self, field_errors=None, form_errors=None):
        super(ValidationError, self).__init__("Schema validation error")
        self.field_errors = field_errors or []
        self.form_errors = form_errors or []


class FormValidationError(Exception):

    def __init__(self, message):
        self.message = message


class AlreadyExistsError(Exception):

    def __init__(self, message):
        self.message = message


class StateUpdateProhibitedError(Exception):
    pass


class BlobStorageNotImplementedError(Exception):
    pass
