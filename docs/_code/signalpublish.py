from morpfw.crud import signals
from .app import App
from .model import PageModel

MYSIGNAL = 'my_signal'


@App.view(model=PageModel, name='dispatch')
def dispatch(request, context):
    request.app.signal_publish(request, context, MYSIGNAL)


@App.subscribe(model=PageModel, signal=MYSIGNAL)
def handle_signal(request, context, signal):
    print("hello world!")
