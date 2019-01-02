import morepath
from more.jwtauth import JWTIdentityPolicy
from morpfw.crud import App as CRUDApp
import reg
import dectate
from morepath.reify import reify
import json
from typing import List, Optional, Type
import morpfw
from ...app import BaseApp

_REGISTERED_APPS: List[morepath.App] = []


class App(BaseApp):
    pass
