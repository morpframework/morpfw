import morepath
import reg

from .model import Collection, Model


class WorkflowCollection(Collection):
    pass


class WorkflowModel(Model):
    @classmethod
    def transition(klass, model):
        def apply_transition(func):
            klass._apply_transition.subscribe(obj=model, request=morepath.Request)(func)

        return apply_transition

    @reg.dispatch_method(
        reg.match_instance("obj"), reg.match_instance("request"),
    )
    def _apply_transition(self, obj, request):
        pass

    def process(self, obj):
        self._apply_transition.publish(self, obj, self.request)
