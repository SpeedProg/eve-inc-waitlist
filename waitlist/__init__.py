from datetime import datetime
from json import JSONEncoder

from flask import Flask
from flask_cdn import CDN
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_principal import Principal
from os import path
import os
import stat
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_seasurf import SeaSurf
from sqlalchemy import MetaData

from waitlist.utility import config
from waitlist.utility.babili import BabiliFilter
from flask_htmlmin import HTMLMIN
from flask_assets import Environment
from webassets.filter import register_filter
from flask_limiter.extension import Limiter
from flask_limiter.util import get_ipaddr

app = Flask(import_name=__name__, static_url_path="/static",
            static_folder="../static", template_folder=path.join("..", "templates"))
app.secret_key = config.secret_key

# flask config
app.config['SESSION_TYPE'] = 'filesystem'
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = config.secure_cookies
app.config['SESSION_COOKIE_SECURE'] = config.secure_cookies
app.config['UPLOAD_FOLDER'] = path.join(".", "sde")
# make sure the upload folder actually exists
# give owner read, write, list(execute)
os.makedirs(app.config['UPLOAD_FOLDER'], mode=(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR), exist_ok=True)

# sqlalchemy config
app.config['SQLALCHEMY_DATABASE_URI'] = config.connection_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = config.sqlalchemy_pool_recycle

# flask cdn config
app.config['CDN_DOMAIN'] = config.cdn_domain
app.config['CDN_HTTPS'] = config.cdn_https
app.config['CDN_TIMESTAMP'] = False

# flask assets config
app.config['FLASK_ASSETS_USE_CDN'] = config.cdn_assets
app.config['ASSETS_DEBUG'] = config.assets_debug

# flask HTMLMIN config
app.config['MINIFY_PAGE'] = config.html_min

# naming conventions for sql

convention = {
  "ix": "ix_%(column_0_label)s",
  "uq": "uq_%(table_name)s_%(column_0_name)s",
  "ck": "ck_%(table_name)s_%(constraint_name)s",
  "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
  "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)

# init SQLAlchemy
db = SQLAlchemy(app, metadata=metadata)

# init login manager
login_manager = LoginManager()
login_manager.init_app(app)

# init flask principal
principals = Principal(app)

# init sqlmigration manager
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)

# init SeaSurf
seasurf = SeaSurf(app)

# init flask CDN
CDN(app)

# init flask HTMLMIN
HTMLMIN(app)

# init assets environment
assets = Environment(app)
register_filter(BabiliFilter)


class MiniJSONEncoder(JSONEncoder):
    """Minify JSON output."""
    item_separator = ','
    key_separator = ':'

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()+"Z"
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, obj)

app.json_encoder = MiniJSONEncoder

# init rate limiting
limiter = Limiter(key_func=get_ipaddr, storage_uri="memory://", strategy="moving-window")
limiter.init_app(app)
