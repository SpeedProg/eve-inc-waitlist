import os
import base64
from os import makedirs
from configparser import ConfigParser

from waitlist.data import version


def set_if_not_exists(self, section, option, value):
    if not self.has_option(section, option):
        self.set(section, option, value)


ConfigParser.set_if_not_exists = set_if_not_exists

config = ConfigParser()

if os.path.isfile(os.path.join(".", "config", "config.cfg")):
    config.read(os.path.join(".", "config", "config.cfg"))
else:
    # make sure the directory exists
    if not os.path.isdir(os.path.join(".", "config")):
        makedirs(os.path.join(".", "config"))
    
# database section
if not config.has_section("database"):
    config.add_section("database")

config.set_if_not_exists("database", "connection_uri", "mysql+mysqldb://user:password@localhost:3306/dbname")
config.set_if_not_exists("database", "sqlalchemy_pool_recycle", "7200")

if not config.has_section("app"):
    config.add_section("app")
config.set_if_not_exists("app", "secret_key", base64.b64encode(os.urandom(24)).decode('utf-8', 'strict'))
config.set_if_not_exists("app", "server_port", "81")
config.set_if_not_exists("app", "server_bind", "0.0.0.0")
config.set_if_not_exists("app", "community_name", "IncWaitlist")
config.set_if_not_exists("app", "user_agent", "Bruce Warhead: Eve Incursion Waitlist")
config.set_if_not_exists("app", "domain", "localhost")

if not config.has_section("logging"):
    config.add_section("logging")
config.set_if_not_exists("logging", "error_file", "/var/log/pywaitlist/error.log")
config.set_if_not_exists("logging", "info_file", "/var/log/pywaitlist/info.log")
config.set_if_not_exists("logging", "access_file", "/var/log/pywaitlist/access.log")
config.set_if_not_exists("logging", "debug_file", "/var/log/pywaitlist/debug.log")

if not config.has_section("crest"):
    config.add_section("crest")
config.set_if_not_exists("crest", "client_id", "f8934rsdf")
config.set_if_not_exists("crest", "client_secret", "f893ur3")
config.set_if_not_exists("crest", "return_url", "")

if not config.has_section("motd"):
    config.add_section("motd")
config.set_if_not_exists("motd", "hq", "..")
config.set_if_not_exists("motd", "vg", "..")

if not config.has_section("cdn"):
    config.add_section("cdn")
config.set_if_not_exists("cdn", "cdn_domain", "")
config.set_if_not_exists("cdn", "cdn_assets", "False")
config.set_if_not_exists("cdn", "cdn_https", "False")
config.set_if_not_exists("cdn", "eve_img_server", "https://imageserver.eveonline.com/{0}.{1}")
config.set_if_not_exists("cdn", "eve_img_server_webp", "False")

if not config.has_section("cookies"):
    config.add_section("cookies")
config.set_if_not_exists("cookies", "secure_cookies", "False")

if not config.has_section("node"):
    config.add_section("node")
config.set_if_not_exists("node", "node_bin", "")

if not config.has_section("debug"):
    config.add_section("debug")
config.set_if_not_exists("debug", "enabled", "False")

if not config.has_section("security"):
    config.add_section("security")
config.set_if_not_exists("security", "scramble_names", "False")
config.set_if_not_exists("security", "require_auth_for_chars", "False")

if not config.has_section("disable"):
    config.add_section("disable")
config.set_if_not_exists("disable", "teamspeak", "False")

if not config.has_section("pageinfo"):
    config.add_section("pageinfo")
config.set_if_not_exists("pageinfo", "influence_link", "#")

if not config.has_section("fittools"):
    config.add_section("fittools")
config.set_if_not_exists("fittools", "stats_enabled", "True")
config.set_if_not_exists("fittools", "stats_uri", "https://quiescens.duckdns.org/wl/ext/wl_external.js")
config.set_if_not_exists("fittools", "stats_sri", "sha384-VonGhMELp1YLVgnJJMq2NqUOpRjhV7nUpiATMsrK5TIMrYQuGUaUPUZlQIInhGc5")

    
with open(os.path.join(".", "config", "config.cfg"), "w") as configfile:
    config.write(configfile)

title = config.get("app", "community_name")

debug_enabled = config.get("debug", "enabled") == "True"
node_bin = config.get("node", "node_bin")
connection_uri = config.get("database", "connection_uri")
secure_cookies = config.get("cookies", "secure_cookies") == "True"
cdn_https = config.get("cdn", "cdn_https") == "True"
cdn_domain = config.get("cdn", "cdn_domain")
cdn_assets = config.get("cdn", "cdn_assets") == "True"
cdn_eveimg = config.get("cdn", "eve_img_server")
cdn_eveimg_webp = config.get("cdn", "eve_img_server_webp") == "True"

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

scramble_names = config.get("security", "scramble_names") == "True"
require_auth_for_chars = config.get("security", "require_auth_for_chars") == "True"

disable_teamspeak = config.get("disable", "teamspeak") == "True"

influence_link = config.get("pageinfo", "influence_link")

cdn_eveimg_js = cdn_eveimg.format("${ path }", "${ suffix }")

stattool_uri = config.get("fittools", "stats_uri")
stattool_sri = config.get("fittools", "stats_sri")
stattool_enabled = config.get("fittools", "stats_enabled") == "True"

user_agent = config.get("app", "user_agent")+"/"+version.version

domain = config.get("app", "domain")
