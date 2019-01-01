from .sqlstorage.sqlstorage import UserSQLStorage


class LDAP3SQLUserStorage(UserSQLStorage):

    def get(self, identifier):
        raise NotImplementedError

    def get_by_userid(self, userid):
        raise NotImplementedError

    def get_by_username(self, username):
        raise NotImplementedError

    def change_password(self, userid, new_password):
        raise NotImplementedError

    def validate(self, userid, password):
        raise NotImplementedError
