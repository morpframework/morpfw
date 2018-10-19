from .ext.authmanager.app import App
from .ext.authmanager import UserCollection
from .ext.authmanager import GroupCollection
from .ext.authmanager import permission as authperm
from .crud import permission as jslperm


def _has_admin_role(app, identity, context, permission):
    return app.authmanager_has_role(context.request, 'administrator')


App.permission_rule(model=UserCollection,
                    permission=authperm.Register)(_has_admin_role)
App.permission_rule(model=UserCollection,
                    permission=jslperm.All)(_has_admin_role)
App.permission_rule(model=GroupCollection,
                    permission=jslperm.All)(_has_admin_role)
