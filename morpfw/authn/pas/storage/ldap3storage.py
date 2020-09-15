import typing
from uuid import uuid4

import ldap
import ldap.ldapobject
import webob.exc

from .sqlstorage.sqlstorage import UserSQLStorage

_marker = object()


class LDAP3SQLUserStorage(UserSQLStorage):
    def __init__(
        self,
        request,
        ldap_uri: str,
        base_dn: str,
        bind_dn: typing.Optional[str] = None,
        bind_password: typing.Optional[str] = None,
        search_scope=ldap.SCOPE_SUBTREE,
        start_tls: bool = True,
        username_attr: str = "uid",
        email_attr: str = "mail",
        attributes: str = None,
        filterstr: str = r"(&(objectClass=inetOrgPerson)(uid={username}))",
        blobstorage=None,
    ):
        self.ldap_base_dn = base_dn
        self.ldap_uri = ldap_uri
        self.ldap_start_tls = start_tls
        self.ldap_username_attr = username_attr
        self.ldap_email_attr = email_attr
        self.ldap_search_scope = search_scope
        self.ldap_attr_mapping = [
            v.split("=") for v in (attributes or "").strip().split(",") if v
        ]
        filterstr = filterstr.strip()
        if not filterstr.startswith("(") and not filterstr.endswith(")"):
            filterstr = "(%s)" % filterstr
        self.ldap_filterstr = filterstr
        self.ldap_default_timezone = "UTC"
        self.ldap_client = self.ldap_connect()
        self.ldap_client.bind_s(bind_dn, bind_password)
        super().__init__(request, blobstorage=blobstorage)

    def ldap_connect(self):
        conn = ldap.initialize(self.ldap_uri)
        if self.ldap_start_tls:
            conn.start_tls_s()
        return conn

    def ldap_get_user(self, username):
        attrs = [self.ldap_username_attr, self.ldap_email_attr] + [
            x[0] for x in self.ldap_attr_mapping
        ]

        try:
            result = self.ldap_client.search_ext_s(
                self.ldap_base_dn,
                self.ldap_search_scope,
                filterstr=self.ldap_filterstr.replace(r"{username}", username),
                attrlist=attrs,
                sizelimit=100,
            )
        except ldap.NO_SUCH_OBJECT:
            return None

        if not result:
            return None

        userdata = {"dn": result[0]}
        for attr in attrs:
            userdata[attr] = result[0][1][attr]
        return userdata

    def get_by_username(self, collection, username):
        user = super().get_by_username(collection, username)
        if user is None:
            ldapuser = self.ldap_get_user(username)
            if ldapuser:
                random_passwd = uuid4().hex
                user = collection.create(
                    {
                        "username": ldapuser[self.ldap_username_attr][0].decode("utf8"),
                        "email": ldapuser[self.ldap_email_attr][0].decode("utf8"),
                        "source": "ldap",
                        "timezone": self.ldap_default_timezone,
                        "password": random_passwd,
                    },
                )
        return user

    def change_password(self, collection, userid, new_password):
        user = super().get_by_userid()
        if user["source"] == "ldap":
            raise webob.exc.HTTPForbidden()
        raise super().change_password(collection, userid, new_password)

    def validate(self, collection, userid, password):
        user = super().get_by_userid(collection, userid)
        if user["source"] == "ldap":
            ldap_client = self.ldap_connect()
            dn = "%s=%s,%s" % (
                self.ldap_username_attr,
                user["username"],
                self.ldap_base_dn,
            )
            try:
                ldap_client.bind_s(dn, password)
            except ldap.INVALID_CREDENTIALS:
                return False
            return True
        return super().validate(collection, userid, password)
