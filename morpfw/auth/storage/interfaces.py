import abc


class IUserStorage(abc.ABC):

    @abc.abstractmethod
    def get_userid(self, model):
        """return the userid that will be used for internal references"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_email(self, email):
        """return UserModel from email address"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_userid(self, userid):
        """return UserModel from userid"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_username(self, username):
        """return UserModel from username"""
        raise NotImplementedError

    @abc.abstractmethod
    def change_password(self, userid, new_password):
        """update user's password"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_groups(self, userid):
        """get groups which the userid is a member of"""
        raise NotImplementedError

    @abc.abstractmethod
    def validate(self, userid, password):
        """validate userid's password"""
        raise NotImplementedError


class IGroupStorage(abc.ABC):

    @abc.abstractmethod
    def get_user_by_userid(self, userid, as_model=True):
        """
        get user by its userid, and return
        as UserModel if as_model is True
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_by_username(self, username, as_model=True):
        """
        get user by its username, and return
        as UserModel if as_model is True
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_members(self, groupname):
        """get list of members of specified group"""
        raise NotImplementedError

    @abc.abstractmethod
    def add_group_members(self, groupname, userids):
        """add userids into a group"""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_group_members(self, groupname, userids):
        """remove userids from group"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_group_user_roles(self, groupname, userid):
        """get roles of userid in group"""
        raise NotImplementedError

    @abc.abstractmethod
    def grant_group_user_role(self, groupname, userid, rolename):
        """grant userid role in group"""
        raise NotImplementedError

    @abc.abstractmethod
    def revoke_group_user_role(self, groupname, userid, rolename):
        """revoke userid role in group"""
        raise NotImplementedError
