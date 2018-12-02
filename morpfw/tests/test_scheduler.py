# FIXME: this test should run properly as unit test
from .common import get_client
from morpfw.app import SQLApp
import morpfw
import pytest
import morepath


class App(SQLApp):
    pass


@App.cron(name='test-cron')
def tick():
    print('tick!')


def main():
    morepath.autoscan()
    morepath.scan()
    App.commit()
    beat = App.celery.Beat()
    beat.run()


if __name__ == '__main__':
    import test_scheduler
    test_scheduler.main()
