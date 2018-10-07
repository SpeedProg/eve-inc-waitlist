import gevent_patch_helper
import logging.config
import os
import json

# setup logging
logger_config = os.path.join('.', 'config', 'logger.base.json')
if os.path.isfile(logger_config):
    with open(logger_config, 'r') as fp:
        cfg = json.load(fp)
        logging.config.dictConfig(cfg)

logger_config = os.path.join('.', 'config', 'logger.user.json')
if os.path.isfile(logger_config):
    with open(logger_config, 'r') as fp:
        cfg = json.load(fp)
        logging.config.dictConfig(cfg)

from werkzeug.contrib.fixers import ProxyFix
from gevent.pywsgi import WSGIServer

from waitlist.blueprints.fittings import bp_waitlist
from waitlist.blueprints.fc_sso import bp as fc_sso_bp
from waitlist.blueprints.fleet import bp as fleet_bp
from waitlist.blueprints.api.fleet import bp as api_fleet_bp
from waitlist.blueprints.api.fittings import bp as api_wl_bp
from waitlist.blueprints.api.teamspeak import bp as api_ts3_bp
from waitlist.blueprints.settings.mail import bp as settings_mail_bp
from waitlist.blueprints.settings.fleet_motd import bp as fmotd_bp
from waitlist.blueprints.reform import bp as bp_fleet_reform
from waitlist.blueprints.history.comphistory import bp as bp_comphistory_search
from waitlist.blueprints.api.history import bp as bp_api_history
from waitlist.blueprints.settings.inserts import bp as bp_inserts
from waitlist.blueprints.api.openwindow import bp as bp_openwindow
from waitlist.blueprints.api.sse import bp as bp_sse
from waitlist.blueprints.api.waitlist import bp as bp_waitlists
from waitlist.blueprints.accounts.commandcore import bp as bp_commandcore
from waitlist.blueprints.accounts.profile import bp as bp_profile
from waitlist.blueprints.api.mail import bp as bp_esi_mail
from waitlist.blueprints.api.ui import bp as bp_esi_ui
from waitlist.blueprints.calendar.settings import bp as bp_calendar_settings
from waitlist.blueprints.cc_vote import bp as bp_ccvote
from waitlist.blueprints.settings.ccvote_results import bp as bp_ccvote_settings
from waitlist.blueprints.fleetview import bp as bp_fleetview

from waitlist.blueprints.settings import accounts as settings_accounts, bans, fleet_motd, fleetoptions, inserts, mail, overview,\
    staticdataimport, teamspeak, permissions
from waitlist.blueprints import trivia, feedback, swagger_api
from waitlist.blueprints.api import permission
from waitlist.blueprints import xup
from waitlist.blueprints import notification
# needs to he here so signal handler gets registered
from waitlist.signal import handler

# load the jinja2 hooks
from waitlist.utility.jinja2 import *

# load flask hooks
from waitlist.utility.flask import *

# load base app routes
from waitlist.blueprints import *

app.register_blueprint(bp_waitlist)
app.register_blueprint(feedback.feedback, url_prefix="/feedback")
app.register_blueprint(fc_sso_bp, url_prefix="/fc_sso")
app.register_blueprint(fleet_bp, url_prefix="/fleet")
app.register_blueprint(api_fleet_bp, url_prefix="/api/fleet")
app.register_blueprint(api_wl_bp, url_prefix="/api/fittings")
app.register_blueprint(api_ts3_bp, url_prefix="/api/ts3")
app.register_blueprint(settings_mail_bp, url_prefix="/settings/mail")
app.register_blueprint(fmotd_bp, url_prefix="/settings/fmotd")
app.register_blueprint(bp_fleet_reform, url_prefix="/fleet/reform")
app.register_blueprint(bp_comphistory_search, url_prefix="/history/comp_search")
app.register_blueprint(bp_api_history, url_prefix="/api/history")
app.register_blueprint(bp_inserts, url_prefix="/settings/inserts")
app.register_blueprint(bp_openwindow, url_prefix="/api/ui/openwindow")
app.register_blueprint(bp_sse, url_prefix="/api/sse")
app.register_blueprint(bp_waitlists, url_prefix="/api/public/waitlists")
app.register_blueprint(bp_commandcore, url_prefix="/accounts/cc")
app.register_blueprint(bp_profile, url_prefix="/accounts/profile")
app.register_blueprint(bp_esi_mail, url_prefix="/api/esi/mail")
app.register_blueprint(bp_esi_ui, url_prefix="/api/esi/ui")
app.register_blueprint(bp_calendar_settings, url_prefix="/settings/calendar")
app.register_blueprint(bp_ccvote, url_prefix="/ccvote")
app.register_blueprint(bp_ccvote_settings, url_prefix="/settings/ccvote")
app.register_blueprint(bp_fleetview, url_prefix="/fleetview")
app.register_blueprint(trivia.submission.bp, url_prefix="/trivia")

# settings blueprints
app.register_blueprint(settings_accounts.bp, url_prefix='/settings/accounts')
app.register_blueprint(bans.bp, url_prefix='/settings/bans')
app.register_blueprint(fleet_motd.bp, url_prefix='/settings/motd')
app.register_blueprint(fleetoptions.bp, url_prefix='/settings/fleet')
app.register_blueprint(inserts.bp, url_prefix='/settings/inserts')
app.register_blueprint(mail.bp, url_prefix='/settings/mail')
app.register_blueprint(overview.bp, url_prefix='/settings')
app.register_blueprint(staticdataimport.bp, url_prefix='/settings/sde')
app.register_blueprint(teamspeak.bp, url_prefix='/settings/teamspeak')
app.register_blueprint(permissions.bp, url_prefix='/settings/permissions')
app.register_blueprint(permission.bp, url_prefix='/api/permission')
app.register_blueprint(xup.bp, url_prefix='/xup')

# notification
app.register_blueprint(notification.bp, url_prefix="/notification")

logger = logging.getLogger(__name__)


def run_server():
    app.wsgi_app = ProxyFix(app.wsgi_app)
    wsgi_logger = logging.getLogger("gevent.pywsgi.WSGIServer")
    server = WSGIServer((config.server_bind, config.server_port), app,
                        log=wsgi_logger, error_log=wsgi_logger)
    server.serve_forever()


if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=81, debug=True)

    # connect account signal handler
    handler.account.connect()
    run_server()
