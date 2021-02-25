import morpfw

settings = {
    "application": {
        "title": "My App",  # app title
        "class": "app:App",  # import path to your app
    }
}

with morpfw.request_factory(settings) as request:
    # do something here with the request
    pass
