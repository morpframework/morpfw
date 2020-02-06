import typing
from dataclasses import dataclass

from ...app import App
from ..model import Model
from .base import XattrProvider

_marker = object()


class FieldXattrProvider(XattrProvider):

    field = "xattrs"

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
