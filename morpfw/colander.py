import colander
from cryptography.fernet import Fernet


class EncryptedExportField(colander.String):
    """ 
    Serialize non-encrypted appstruct into encrypted cstruct. 
    """

    def __init__(self, fernet_key, *args, **kwargs):
        self.fernet_key = fernet_key
        self.fernet = Fernet(fernet_key)
        super().__init__(*args, **kwargs)

    def serialize(self, node, appstruct):
        v = super().serialize(node, appstruct)
        if v is colander.null:
            return v
        if v.strip():
            if v == "data":
                raise Exception()
            return self.fernet.encrypt(v.encode("utf8")).decode("utf8")
        return colander.null

    def deserialize(self, node, cstruct):
        v = super().deserialize(node, cstruct)
        if v is colander.null:
            return v
        # encrypt
        if v.strip():
            v = self.fernet.decrypt(v.encode("utf8")).decode("utf8")
            return v
        return colander.null


class EncryptedStoreField(colander.String):
    """ 
    Deserialize non-encrypted cstruct into encrypted appstruct. 
    """

    def __init__(self, fernet_key, *args, **kwargs):
        self.fernet_key = fernet_key
        self.fernet = Fernet(fernet_key)
        super().__init__(*args, **kwargs)

    def serialize(self, node, appstruct):
        """ Decrypt appstruct """
        v = super().serialize(node, appstruct)
        if v is colander.null:
            return v
        if v.strip():
            v = self.fernet.decrypt(v.encode("utf8")).decode("utf8")
            return v
        return colander.null

    def deserialize(self, node, cstruct):
        """ Encrypt cstruct """
        v = super().deserialize(node, cstruct)
        if v.strip():
            return self.fernet.encrypt(v.encode("utf8")).decode("utf8")
        return colander.null
