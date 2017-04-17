from gevent import monkey
monkey.patch_all()
from waitlist.utility.swagger.patch import monkey_patch_pyswagger_requests_client
monkey_patch_pyswagger_requests_client()

import logging
from logging.handlers import TimedRotatingFileHandler
from waitlist.blueprints.feedback import feedback
from gevent.pywsgi import WSGIServer
from waitlist import app
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

from waitlist.blueprints.settings import accounts, bans, fleet_motd, fleetoptions, inserts, mail, overview,\
    staticdataimport, teamspeak, permissions
from waitlist.blueprints import trivia
from waitlist.blueprints.api import permission
from waitlist.blueprints.api import fittings
from waitlist.blueprints import xup
# needs to he here so signal handler gets registered
from waitlist.signal.handler import acc_created, roles_changed, account_status_change

app.register_blueprint(bp_waitlist)
app.register_blueprint(feedback, url_prefix="/feedback")
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
app.register_blueprint(accounts.bp, url_prefix='/settings/accounts')
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
app.register_blueprint(fittings.bp, url_prefix='/api/fittings')
app.register_blueprint(xup.bp, url_prefix='/xup')


logger = logging.getLogger(__name__)

# load the jinja2 hooks
from waitlist.utility.jinja2 import *

# load flask hooks
from waitlist.utility.flask import *

# load base app routes
from waitlist.blueprints import *

err_fh = None
info_fh = None
access_fh = None
debug_fh  = None


#@werkzeug.serving.run_with_reloader
def runServer():
    wsgi_logger = logging.getLogger("gevent.pywsgi.WSGIServer")
    wsgi_logger.addHandler(err_fh)
    wsgi_logger.addHandler(access_fh)
    wsgi_logger.setLevel(logging.INFO)
    server = WSGIServer((config.server_bind, config.server_port), app, log=wsgi_logger, error_log=wsgi_logger)
    server.serve_forever()

if __name__ == '__main__':
    err_fh = TimedRotatingFileHandler(filename=config.error_log, when="midnight", interval=1, utc=True)
    info_fh = TimedRotatingFileHandler(filename=config.info_log, when="midnight", interval=1, utc=True)
    access_fh = TimedRotatingFileHandler(filename=config.access_log, when="midnight", interval=1, utc=True)
    debug_fh = TimedRotatingFileHandler(filename=config.debug_log, when="midnight", interval=1, utc=True)

    formatter = logging\
        .Formatter('%(asctime)s - %(name)s - %(levelname)s - %(pathname)s - %(funcName)s - %(lineno)d - %(message)s')
    err_fh.setFormatter(formatter)
    info_fh.setFormatter(formatter)
    access_fh.setFormatter(formatter)
    debug_fh.setFormatter(formatter)

    info_fh.setLevel(logging.INFO)
    err_fh.setLevel(logging.ERROR)
    debug_fh.setLevel(logging.DEBUG)

    waitlistlogger = logging.getLogger("waitlist")
    waitlistlogger.addHandler(err_fh)
    waitlistlogger.addHandler(info_fh)
    waitlistlogger.addHandler(debug_fh)
    waitlistlogger.setLevel(logging.INFO)

    app.logger.addHandler(err_fh)
    app.logger.addHandler(info_fh)
    app.logger.addHandler(debug_fh)
    app.logger.setLevel(logging.INFO)
    
    # app.run(host="0.0.0.0", port=81, debug=True)
    runServer()
