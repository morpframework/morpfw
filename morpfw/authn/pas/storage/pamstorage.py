# FIXME: this plugin is not testable

import pamela
from .sqlstorage.sqlstorage import UserSQLStorage, APIKeySQLStorage, GroupSQLStorage
from ..user.model import UserModel, UserSchema
from ..group.model import GroupModel, GroupSchema
from ..apikey.model import APIKeyModel, APIKeySchema
from ....crud.errors import UnprocessableError
import socket
from ..app import App


class UserPAMSQLStorage(UserSQLStorage):

    def get(self, identifier):
        try:
            pamela.check_account(identifier)
        except pamela.PAMError:
            return None
        user = super().get(identifier)
        if not user:
            user = self.create({
                'username': identifier,
                'email': '%s@%s' % (identifier, socket.gethostname())
            })
        return user

    def validate(self, userid, password):
        u = self.get_by_userid(userid)
        return pamela.authenticate(username=u.data['username'],
                                   password=password)

    def change_password(self, userid, new_password):
        raise UnprocessableError(
            'Changing password is not possible for PAM auth')
