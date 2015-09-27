from edgarweb            import app, login_manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.script    import Manager

manager   = Manager  (app)
bootstrap = Bootstrap(app)

login_manager.init_app(app)
login_manager.login_view = 'login'

manager.run()

