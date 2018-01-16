import abc


class IStorage(abc.ABCMeta):

    @abc.abstractmethod
    def search_users(self, filters):
        "return list of users"
        raise NotImplementedError

    @abc.abstractmethod
    def search_groups(self, filters):
        "return list of groups"
        raise NotImplementedError

    @abc.abstractmethod
    def get_user(self, username):
        """
        get specific user model

        return User object
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_user(self, username, password, attrs):
        """
        create a user

        return User object
        """
        raise NotImplementedError

    @abc.abstractmethod
    def validate(self, username, password):
        """
        validate user authentication

        return boolean
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_group(self, groupname, attrs=None):
        """
        create a group

        return Group object
        raises ValueError if group already exists
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_group(self, groupname):
        """
        get group by name

        return Group object
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_members(self, groupname):
        """
        get list of members of group

        return list of User objects        
        """
        raise NotImplementedError

    @abc.abstractmethod
    def add_group_members(self, groupname, usernames):
        """
        add list of usernames into group
        ignore if already exists in group

        return None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def remove_group_members(self, groupname, usernames):
        """
        remove list of usernames from group
        ignore if doesnt exists in group

        return None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_group_user_roles(self, groupname, username):
        """
        get list of roles mapping in a group for user

        return list of role string
        """
        raise NotImplementedError

    @abc.abstractmethod
    def grant_group_user_role(self, groupname, username, rolename):
        """
        grant role in group to username
        ignore if role already granted

        return None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def revoke_group_user_role(self, groupname, username, rolename):
        """
        revoke role in group from username
        ignore if role doesn't exist

        return None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_groups(self, username):
        """
        search for group for specified user

        return a list of Group objects
        """
        raise NotImplementedError
