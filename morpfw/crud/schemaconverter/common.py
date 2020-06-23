import copy
import typing

_marker = object()


def drop_empty(schema, data):
    result = {}
    for attr, prop in sorted(schema.__dataclass_fields__.items(), key=lambda x: x[0]):
        if data.get(attr, None) is None:
            if prop.metadata.get("exclude_if_empty", None) is True:
                continue
        result[attr] = copy.deepcopy(data[attr])
    return result


def dataclass_get_type(field, exclude_if_empty=True):
    metadata = {
        "required": _marker,
        "exclude_if_empty": exclude_if_empty,
        "validators": [],
    }

    metadata.update(field.metadata)

    origin = getattr(field.type, "__origin__", None)
    required = True
    if origin == typing.Union:
        if len(field.type.__args__) == 2:
            if field.type.__args__[1] == type(None):
                required = False
            typ = field.type.__args__[0]
    else:
        typ = field.type

    if metadata["required"] is _marker:
        metadata["required"] = required

    if field.metadata.get("required", None) is not None:
        metadata["required"] = field.metadata["required"]

    required = metadata["required"]

    origin = getattr(typ, "__origin__", None)

    if origin == list:
        if getattr(typ, "__args__", None):
            return {
                "name": field.name,
                "type": list,
                "schema": field.type.__args__[0],
                "required": required,
                "metadata": metadata,
            }
        else:
            return {
                "name": field.name,
                "type": list,
                "required": required,
                "metadata": metadata,
            }

    return {"type": typ, "required": required, "metadata": metadata}


def dataclass_check_type(field, basetype):

    t = dataclass_get_type(field)

    if t["type"] == basetype:
        return t

    # wtf bool is a subclass of integer?
    if t["type"] == bool and basetype == int:
        return None

    if issubclass(t["type"], basetype):
        return t

    return None
