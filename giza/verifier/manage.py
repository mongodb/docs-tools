import os, sys
from flask.ext.script import Manager, Server
from app import flask_app
app = flask_app.app

from app import views
from app import filters

if __name__ == "__main__":
    manager = Manager(app)

    # Turn on debugger by default and reloader
    manager.add_command("runserver", Server(
        use_debugger = True,
        use_reloader = True,
        host = '0.0.0.0')
    )
    manager.run()
