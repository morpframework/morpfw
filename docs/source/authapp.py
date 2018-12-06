import morpfw


class App(morpfw.SQLApp):
    pass


class MountedApp(morpfw.SQLApp):
    pass


@App.mount(app=MountedApp, path='/api/v1')
def mount_app(app):
    return MountedApp()


if __name__ == '__main__':
    morpfw.run(App, {})
