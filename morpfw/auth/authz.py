

class NullPolicy(object):

    def has_role(self, request, rolename, username=None, groupname='__default__'):
        return True
