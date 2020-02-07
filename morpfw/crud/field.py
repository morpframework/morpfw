from copy import copy, deepcopy
from dataclasses import field

MISSING = object()


class Field(object):
    def __init__(self, metadata=None):
        self.metadata = metadata or {}
        self.metadata.setdefault("required", False)
        self.metadata.setdefault("editable", True)
        self._default = MISSING
        self._default_factory = MISSING

    def default(self, value):
        self._default = value
        return self

    def default_factory(self, value):
        self._default_factory = value
        return self

    def required(self, required=True):
        self.metadata["required"] = required
        return self

    def editable(self, editable=True):
        self.metadata["editable"] = editable
        return self

    def init(self):
        if self._default is not MISSING:
            return field(default=self._default, metadata=self.metadata)
        if self._default_factory is not MISSING:
            return field(default_factory=self._default_factory, metadata=self.metadata)
        return field(metadata=self.metadata)

    def widget(self, widget):
        self.metadata["deform.widget"] = widget
        return self

    def unique(self):
        self.metadata["unique"] = True
        return self
