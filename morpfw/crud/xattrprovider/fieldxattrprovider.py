from dataclasses import dataclass
from .base import XattrProvider
from ..model import Model
from ...app import App
import typing

_marker = object()


@dataclass
class DefaultXattrSchema(object):
    pass


class FieldXattrProvider(XattrProvider):

    field = 'xattrs'

    schema: typing.Type[typing.Any] = DefaultXattrSchema
    additional_properties = True

    def __getitem__(self, key):
        return self.context[self.field][key]

    def __setitem__(self, key, value):
        data = self.context[self.field]
        data[key] = value
        self.context.update({self.field: data})

    def __delitem__(self, key):
        data = self.context[self.field]
        del data[key]
        self.context.update({self.field: data})

    def get(self, key, default=_marker):
        if default is _marker:
            return self.context[self.field].get(key)
        return self.context[self.field].get(key, default)

    def as_json(self):
        return self.context.as_json().get(self.field, {})

    def as_dict(self):
        return self.context[self.field] or {}

    def update(self, newdata: dict):
        data = self.context[self.field] or {}
        data.update(newdata)
        self.context.update({self.field: data})


@App.xattrprovider(model=Model)
def get_default_xattrprovider(context):
    return FieldXattrProvider(context)
