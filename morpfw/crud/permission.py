from ..permission import All as MFWAll

class All(MFWAll):
    pass

class Create(All):
    pass

class View(Create):
    pass

class Edit(All):
    pass

class Delete(All):
    pass

class Search(All):
    pass

class Aggregate(All):
    pass

class StateUpdate(MFWAll):
    pass
