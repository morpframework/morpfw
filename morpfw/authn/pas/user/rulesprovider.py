from ....crud.rulesprovider.base import RulesProvider
from .. import exc
from ..app import App
from ..utils import has_role
from .model import UserCollection, UserModel


class UserRulesProvider(RulesProvider):

    context: UserModel

    def change_password(self, password: str, new_password: str, secure: bool = True):
        context = self.context
        if secure and not has_role(self.request, "administrator"):
            if not context.validate(password, check_state=False):
                raise exc.InvalidPasswordError(context.userid)
        context.storage.change_password(context, context.identity.userid, new_password)

    def validate(self, password: str, check_state=True) -> bool:
        context = self.context
        if check_state and context.data["state"] != "active":
            return False
        return context.storage.validate(context, context.userid, password)


@App.rulesprovider(model=UserModel)
def get_user_rulesprovider(context):
    return UserRulesProvider(context)
