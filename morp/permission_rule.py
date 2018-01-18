from .authmanager.app import App
from .authmanager import UserCollection
from .authmanager import GroupCollection
from .authmanager import permission as authperm
from .jslcrud import permission as jslperm


def _has_admin_role(app, identity, context, permission):
    return app.authmanager_has_role(context.request, 'administrator')


App.permission_rule(model=UserCollection,
                    permission=authperm.Register)(_has_admin_role)
App.permission_rule(model=UserCollection,
                    permission=jslperm.All)(_has_admin_role)
App.permission_rule(model=GroupCollection,
                    permission=jslperm.All)(_has_admin_role)
