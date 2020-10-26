from datetime import datetime
from json import JSONEncoder

from flasgger import Swagger, LazyString, LazyJSONEncoder
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
from flask.globals import request
from waitlist.utility.assets import register_asset_bundles
from flask_babel import Babel
from waitlist.utility.i18n.locale import get_locale, get_langcode_from_locale
from waitlist.utility.webassets.filter.cssoptimizer import CSSOptimizerFilter

app = Flask(import_name=__name__, static_url_path="/static",
            static_folder="../static", template_folder=path.join("..", "templates"))
app.secret_key = config.secret_key

# set jinja2 options
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

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

# seasurf config
app.config['CSRF_COOKIE_SECURE'] = config.secure_cookies
app.config['CSRF_COOKIE_HTTPONLY'] = True

# flask cdn config
app.config['CDN_DOMAIN'] = config.cdn_domain
app.config['CDN_HTTPS'] = config.cdn_https
app.config['CDN_TIMESTAMP'] = False

# flask assets config
app.config['FLASK_ASSETS_USE_CDN'] = config.cdn_assets
app.config['ASSETS_DEBUG'] = config.assets_debug

# flask HTMLMIN config
app.config['MINIFY_PAGE'] = config.html_min

# language config
app.config['LANGUAGES'] = ['en', 'de']
app.config['BABEL_TRANSLATION_DIRECTORIES'] = '../translations'

babel = Babel(app)

@babel.localeselector
def babel_localeselection():
    return get_langcode_from_locale(get_locale(app))


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
if config.cdn_assets:
    CDN(app)

# init flask HTMLMIN
HTMLMIN(app)

# init assets environment
assets = Environment(app)
assets.auto_build = (config.debug_enabled or config.auto_build)
register_filter(BabiliFilter)
register_filter(CSSOptimizerFilter)
register_asset_bundles(assets)

if not assets.auto_build:
    for bundle in assets:
        bundle.build()

class MiniJSONEncoder(LazyJSONEncoder):
    """Minify JSON output."""
    item_separator = ','
    key_separator = ':'

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()+"Z"
        # Let the base class default method raise the TypeError
        return super(MiniJSONEncoder, self).default(obj)


app.json_encoder = MiniJSONEncoder

# init rate limiting
limiter = Limiter(key_func=get_ipaddr, storage_uri="memory://",
                  strategy="moving-window")
limiter.init_app(app)

app.config['SWAGGER'] = {
    'swagger_version': '2.0',
    'title': 'Swagger Waitlist API',
    'headers': [],
    'specs': [
        {
            'version': '0.0.1',
            'title': 'Api v1',
            'endpoint': 'spec/',
            'description': 'Version 1 of the Swagger Waitlist API',
            'route': '/spec/v1/swagger.json',
            # rule_filter is optional
            # it is a callable to filter the views to extract
            'rule_filter': lambda rule: ('_v1' in rule.endpoint),
            # definition_filter is optional
            # it is a callable to filter the definition models to include
            'definition_filter': lambda definition: (
                'v1_model' in definition.tags)
        }
    ],
    'host': LazyString(lambda: request.host),
    'basePath': '',
    'uiversion': 3,
}

template = {
    "schemes": [LazyString(lambda: request.scheme)]
}

swag = Swagger(app, template=template)

