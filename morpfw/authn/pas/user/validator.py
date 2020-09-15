import pytz

from ....crud.errors import FieldValidationError


def valid_source(request, schema, field, value, mode=None):
    if value not in ["local", "ldap"]:
        return "Only local & ldap source is supported at the moment"


def valid_tz(request, schema, field, value, mode=None):
    if value not in pytz.all_timezones:
        return "Invalid timezone"
