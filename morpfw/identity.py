import pytz

import morepath

from .authn.pas.utils import has_role


class Identity(morepath.Identity):
    def __init__(self, request, userid, **kw):
        self.request = request
        super().__init__(userid, **kw)

    def timezone(self):
        return pytz.UTC

    def is_administrator(self):
        return has_role(self.request, "administrator", userid=self.userid)
