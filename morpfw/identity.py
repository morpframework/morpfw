import morepath
import pytz

class Identity(morepath.Identity):

    def timezone(self):
        return pytz.UTC
