
class ValidationError(Exception):
    def __init__(self, field_errors=None, form_errors=None):
        super(ValidationError, self).__init__("Schema validation error")
        self.field_errors = field_errors or []
        self.form_errors = form_errors or []


class FormValidationError(object):

    def __init__(self, message):
        self.message = message


class AlreadyExistsError(Exception):

    def __init__(self, message):
        self.message = message


class NotFoundError(Exception):

    def __init__(self, model, identifier):
        self.model = model
        self.identifier = identifier
        self.message = "%s:%s:%s" % (
            model.__module__, model.__name__, identifier)


class StateUpdateProhibitedError(Exception):
    pass
