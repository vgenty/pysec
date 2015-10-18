from flask  import Flask
from celery import Celery

app = Flask(__name__,instance_relative_config=True)

app.config.from_object(  'config'  )
app.config.from_pyfile( 'config.py')

from flask.ext.login import LoginManager
login_manager = LoginManager()

app.config['CELERY_BROKER_URL']     = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['CELERYD_PREFETCH_MULTIPLIER'] = 128

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

from .views.login       import login
from .views.datadisplay import datadisplay

app.register_blueprint(    login   )
app.register_blueprint( datadisplay )

celery.conf.update(app.config)

