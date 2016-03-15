from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_principal import Principal
from os import path
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
import os
from flask_seasurf import SeaSurf
from waitlist.utility import config

basedir = path.abspath(path.dirname(__file__))

app = Flask(import_name=__name__, template_folder=path.join("..", "templates"))
app.secret_key = config.secret_key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = config.connection_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = config.sqlalchemy_pool_recycle
login_manager = LoginManager()
login_manager.init_app(app)
principals = Principal(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)
seasurf = SeaSurf(app)
app.config['UPLOAD_FOLDER'] = path.join(".", "sde")
