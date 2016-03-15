import os
import ConfigParser
import base64

if  not os.path.isfile("config.cfg"):
    # create a preset file
    config = ConfigParser.SafeConfigParser()
    config.add_section("database")
    config.set("database", "connection_uri", "mysql+mysqldb://user:password@localhost:3306/dbname")
    config.set("database", "sqlalchemy_pool_recycle", "7200")
    
    config.add_section("app")
    config.set("app", "secret_key", base64.b64encode(os.urandom(24)))
    with open("config.cfg", "wb") as configfile:
        config.write(configfile)

config = ConfigParser.SafeConfigParser()
config.read("config.cfg")

connection_uri = config.get("database", "connection_uri")
sqlalchemy_pool_recycle = config.getint("database", "sqlalchemy_pool_recycle")
secret_key = base64.b64decode(config.get("app", "secret_key"))