from morpfw.crud import pubsub
import reg


def test_signal():

    class Model(object):
        pass

    class SubModel(Model):
        pass

    @reg.dispatch(reg.match_instance('model'),
                  reg.match_key('signal', lambda model, signal: signal))
    def event(model, signal):
        raise NotImplementedError

    @event.subscribe(model=Model, signal='event')
    def one(model, signal):
        return 1

    @event.subscribe(model=Model, signal='event')
    def two(model, signal):
        return 2

    @event.subscribe(model=SubModel, signal='event')
    def three(model, signal):
        return 3

    mobj = Model()
    smobj = SubModel()
    assert list(sorted(event.publish(model=mobj, signal='event'))) == [1, 2]
    assert list(
        sorted(event.publish(model=smobj, signal='event'))) == [1, 2, 3]


def test_event_dispatchmethod():

    class App(object):

        @reg.dispatch_method(reg.match_instance('model'),
                             reg.match_key('signal', lambda self, model, signal: signal))
        def event(self, model, signal):
            raise NotImplementedError

    class Model(object):
        pass

    class SubModel(Model):
        pass

    @App.event.subscribe(model=Model, signal='event')
    def one(app, model, signal):
        return 1

    @App.event.subscribe(model=Model, signal='event')
    def two(app, model, signal):
        return 2

    @App.event.subscribe(model=SubModel, signal='event')
    def three(app, model, signal):
        return 3

    app = App()
    mobj = Model()
    smobj = SubModel()
    assert list(sorted(
        app.event.publish(app, model=mobj, signal='event'))) == [1, 2]
    assert list(sorted(
        app.event.publish(app, model=smobj, signal='event'))) == [1, 2, 3]
