from .auth.app import App
from .auth import UserCollection
from .auth import GroupCollection
from .auth import permission as authperm
from .crud import permission as jslperm


def _has_admin_role(app, identity, context, permission):
    return app.has_role(context.request, 'administrator')


App.permission_rule(model=UserCollection,
                    permission=authperm.Register)(_has_admin_role)
App.permission_rule(model=UserCollection,
                    permission=jslperm.All)(_has_admin_role)
App.permission_rule(model=GroupCollection,
                    permission=jslperm.All)(_has_admin_role)
