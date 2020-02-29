import rulez
import re

valid_identifier_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
valid_namespaced_identifier_pattern = re.compile(r'^[a-z][a-z0-9_\.]*$')

def unique(request, schema, field, value, mode=None):
    if mode=='update':
        return 

    typeinfo = request.app.config.type_registry.get_typeinfo_by_schema(
            schema=schema, request=request)
    collection = typeinfo['collection_factory'](request)
    if collection.search(rulez.field[field] == value):
        return "Already exists"

def valid_identifier(request, schema, field, value, mode=None):
    if not valid_identifier_pattern.match(value):
        return (
            "Only lower cased alphanumeric and _ are accepted and shall"
            " not start with number nor _")


def valid_namespaced_identifier(request, schema, field, value, mode=None):
    if not valid_namespaced_identifier_pattern.match(value):
        return (
            "Only lower cased alphanumeric, . and _ are accepted, and shall"
            " not start with number, . nor _")


