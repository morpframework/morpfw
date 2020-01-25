import abc
from ....interfaces import IModel, IStorageBase
from typing import Optional, Union, List, Sequence


class IUserModel(IModel):
    pass


class IGroupModel(IModel):
    pass


class IUserStorage(IStorageBase):
    @abc.abstractmethod
    def create(self, collection, data) -> IUserModel:
        """
        Create group
        """
        raise NotImplementedError

    @abc.abstractmethod
    def search(
        self,
        collection,
        query: Optional[dict] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: Union[None, list, tuple] = None,
    ) -> List[IUserModel]:
        """return search result based on specified rulez query"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_id(self, collection, id) -> IUserModel:
        """return model from internal ID"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_uuid(self, collection, uuid) -> IUserModel:
        """return model from GUID"""
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, collection, identifier, data: dict):
        """update model with values from data"""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, collection, identifier, model: IUserModel):
        """delete model data"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_userid(self, collection, model: IUserModel) -> str:
        """return the userid that will be used for internal references"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_email(self, collection, email: str) -> IUserModel:
        """return UserModel from email address"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_userid(self, collection, userid: str) -> IUserModel:
        """return UserModel from userid"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_username(self, collection, username: str) -> IUserModel:
        """return UserModel from username"""
        raise NotImplementedError

    @abc.abstractmethod
    def change_password(self, collection, userid: str, new_password: str):
        """update user's password"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_groups(self, collection, userid: str) -> IGroupModel:
        """get groups which the userid is a member of"""
        raise NotImplementedError

    @abc.abstractmethod
    def validate(self, collection, userid: str, password: str) -> bool:
        """validate userid's password"""
        raise NotImplementedError


class IGroupStorage(IStorageBase):
    @abc.abstractmethod
    def create(self, data):
        """
        Create group
        """
        raise NotImplementedError

    @abc.abstractmethod
    def search(
        self,
        query: Optional[dict] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: Union[None, list, tuple] = None,
    ) -> Sequence[IGroupModel]:
        """return search result based on specified rulez query"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_id(self, id) -> IGroupModel:
        """return model from internal ID"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_uuid(self, uuid) -> IGroupModel:
        """return model from GUID"""
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, identifier, data: dict):
        """update model with values from data"""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, identifier, model: IGroupModel):
        """delete model data"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_by_userid(self, userid: str, as_model: bool = True) -> IUserModel:
        """
        get user by its userid, and return
        as UserModel if as_model is True
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_by_username(self, username: str, as_model: bool = True) -> IUserModel:
        """
        get user by its username, and return
        as UserModel if as_model is True
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_members(self, groupname: str) -> List[IUserModel]:
        """get list of members of specified group"""
        raise NotImplementedError

    @abc.abstractmethod
    def add_group_members(self, groupname: str, userids: List[str]):
        """add userids into a group"""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_group_members(self, groupname: str, userids: List[str]):
        """remove userids from group"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_group_user_roles(self, groupname: str, userid: str) -> List[str]:
        """get roles of userid in group"""
        raise NotImplementedError

    @abc.abstractmethod
    def grant_group_user_role(self, groupname: str, userid: str, rolename: str):
        """grant userid role in group"""
        raise NotImplementedError

    @abc.abstractmethod
    def revoke_group_user_role(self, groupname: str, userid: str, rolename: str):
        """revoke userid role in group"""
        raise NotImplementedError
