import os
import ConfigParser
import base64
from os import makedirs

if  not os.path.isfile(os.path.join(".", "config", "config.cfg")):
    # create a preset file
    config = ConfigParser.SafeConfigParser()
    config.add_section("database")
    config.set("database", "connection_uri", "mysql+mysqldb://user:password@localhost:3306/dbname")
    config.set("database", "sqlalchemy_pool_recycle", "7200")
    
    config.add_section("app")
    config.set("app", "secret_key", base64.b64encode(os.urandom(24)))
    config.set("app", "server_port", "81")
    config.set("app", "server_bind", "0.0.0.0")
    
    config.add_section("logging")
    config.set("logging", "error_file", "/var/log/pywaitlist/error.log")
    config.set("logging", "info_file", "/var/log/pywaitlist/info.log")
    config.set("logging", "access_file", "/var/log/pywaitlist/access.log")
    config.set("logging", "debug_file", "/var/log/pywaitlist/debug.log")
    
    config.add_section("crest")
    config.set("crest", "client_id", "f8934rsdf")
    config.set("crest", "client_secret", "f893ur3")
    config.set("crest", "return_url", "")
    
    config.add_section("motd")
    config.set("motd", "hq", "..")
    config.set("motd", "vg", "..")

    config.add_section("cdn")
    config.set("cdn", "cdn_domain", "..")
    config.set("cdn", "cdn_assets", "..")
    config.set("cdn", "cdn_https", "..")

    config.add_section("debug")
    config.set("debug", "fileversion", "")
    config.set("debug", "enabled", "False")
    
    makedirs(os.path.join(".", "config"))
    with open(os.path.join(".", "config", "config.cfg"), "wb") as configfile:
        config.write(configfile)

config = ConfigParser.SafeConfigParser()
config.read(os.path.join("config", "config.cfg"))

debug_enabled = config.get("debug", "enabled") == "True"

connection_uri = config.get("database", "connection_uri")
cdn_https = config.get("cdn", "cdn_https") == "True"
cdn_domain = config.get("cdn", "cdn_domain")
cdn_assets = config.get("cdn", "cdn_assets") == "True"
html_min = not debug_enabled
assets_debug = debug_enabled
sqlalchemy_pool_recycle = config.getint("database", "sqlalchemy_pool_recycle")
secret_key = base64.b64decode(config.get("app", "secret_key"))
server_port = config.getint("app", "server_port")
server_bind = config.get("app", "server_bind")
error_log = config.get("logging", "error_file")
info_log = config.get("logging", "info_file")
access_log = config.get("logging", "access_file")
debug_log = config.get("logging", "debug_file")

crest_client_id = config.get("crest", "client_id")
crest_client_secret = config.get("crest", "client_secret")
crest_return_url = config.get("crest", "return_url")

motd_hq = config.get("motd", "hq")
motd_vg = config.get("motd", "vg")

debug_fileversion = config.get("debug", "fileversion")