from flask import Flask

app = Flask(__name__,instance_relative_config=True)

app.config.from_object('config')
app.config.from_pyfile('config.py')

from flask.ext.login import LoginManager
login_manager = LoginManager()

from .views.login       import login
from .views.datadisplay import datadisplay

app.register_blueprint(    login   )
app.register_blueprint( datadisplay )
