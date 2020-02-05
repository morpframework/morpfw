import typing


class UnprocessableError(Exception):
    def __init__(self, message=None):
        self.message = message or ""


class FormValidationError(Exception):
    def __init__(self, message):
        self.message = message


class FieldValidationError(Exception):
    def __init__(self, path, message):
        self.message = message
        self.path = path


class ValidationError(Exception):
    def __init__(
        self,
        field_errors: typing.Optional[typing.List[FieldValidationError]] = None,
        form_errors: typing.Optional[typing.List[FormValidationError]] = None,
    ):
        super(ValidationError, self).__init__("Schema validation error")
        self.field_errors = field_errors or []
        self.form_errors = form_errors or []


class AlreadyExistsError(Exception):
    def __init__(self, message):
        self.message = message


class StateUpdateProhibitedError(Exception):
    pass


class BlobStorageNotImplementedError(Exception):
    pass
