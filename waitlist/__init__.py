from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_principal import Principal
from os import path
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
import os
from flask_seasurf import SeaSurf

basedir = path.abspath(path.dirname(__file__))

app = Flask(import_name=__name__, template_folder=path.join("..", "templates"))
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
user = "wtm"
password = "wtm"
host = "localhost"
port = 3306
dbname = "wtm"
dbstring = "mysql+mysqldb://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, dbname)
app.config['SQLALCHEMY_DATABASE_URI'] = dbstring
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager()
login_manager.init_app(app)
principals = Principal(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)
seasurf = SeaSurf(app)
