from dateutil.parser import parse as parse_date


class datestr(str):
    def datetime(self):
        return parse_date(self)
