import time

import morpfw
import pytest

# lets setup a skeleton app

class App(morpfw.BaseApp):
    pass


class Root(object):
    pass


@App.path(model=Root, path='')
def get_root(request):
    return Root()


# lets hook up some scheduled job

# run this code every 5 seconds
@App.periodic(name='myproject.every-5-seconds', seconds=5)
def run_5_secs(request_options):
    print('periodic tick!')


# run this code every 1 minute, using cron style scheduling
@App.cron(name='myproject.minutely', minute='*')
def run_every_1_minute(request_options):
    print('cron tick!')
