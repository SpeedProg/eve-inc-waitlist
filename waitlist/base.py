from flask import Flask
from flask_cdn import CDN
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_principal import Principal
from os import path
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_seasurf import SeaSurf
from waitlist.utility import config
from flask_htmlmin import HTMLMIN
from flask.json import JSONEncoder

app = Flask(import_name=__name__, static_url_path="/static", static_folder="../static", template_folder=path.join("..", "templates"))
app.secret_key = config.secret_key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = config.connection_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = config.sqlalchemy_pool_recycle
app.config['CDN_DOMAIN'] = config.cdn_domain
app.config['CDN_HTTPS'] = config.cdn_https
app.config['FLASK_ASSETS_USE_CDN'] = config.cdn_assets
app.config['CDN_TIMESTAMP'] = False
CDN(app)
login_manager = LoginManager()
login_manager.init_app(app)
principals = Principal(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)
seasurf = SeaSurf(app)
app.config['UPLOAD_FOLDER'] = path.join(".", "sde")
app.config['ASSETS_DEBUG'] = True
#app.config['MINIFY_PAGE'] = True
#HTMLMIN(app)

from flask_assets import Environment
assets = Environment(app)

'''
class MiniJSONEncoder(JSONEncoder):
    """Minify JSON output."""
    item_separator = ','
    key_separator = ':'
app.json_encoder = MiniJSONEncoder
'''