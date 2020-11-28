import logging.config
import os
import json


def merge_dicts(destination, source):
    for key, value in source.items():
        if isinstance(value, dict):
            # if there is no dict there we need to create one
            subdict = destination.setdefault(key, {})
            if not isinstance(subdict, dict):
                print('Error merging configs on', key)
            else:
                merge_dicts(subdict, value)
        else:
            destination[key] = value

    return destination


def setup_logging():
    # setup logging
    base_cfg = None
    user_cfg = None
    logger_config = os.path.join('.', 'config', 'logger.base.json')
    if os.path.isfile(logger_config):
        with open(logger_config, 'r') as fp:
            base_cfg = json.load(fp)

    logger_config = os.path.join('.', 'config', 'logger.user.json')
    if os.path.isfile(logger_config):
        with open(logger_config, 'r') as fp:
            user_cfg = json.load(fp)
    # if we have both we need to merge them
    if base_cfg is not None and user_cfg is not None:
        merge_dicts(base_cfg, user_cfg)
    # if there is only user config we can ignore it
    elif user_cfg is not None:
        base_cfg = user_cfg

    logging.config.dictConfig(base_cfg)

def register_blueprints():
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
        staticdataimport, teamspeak, permissions, ship_assignment, murmur
    from waitlist.blueprints import trivia, feedback, swagger_api
    from waitlist.blueprints.api import permission
    from waitlist.blueprints import xup
    from waitlist.blueprints import notification
    from waitlist import flask_hooks


    from waitlist.blueprints import about, login, index

    from waitlist.base import app
    flask_hooks.register_hooks(app)
    swagger_api.register_blueprints()

    app.register_blueprint(bp_waitlist)
    app.register_blueprint(index)
    app.register_blueprint(about.bp)
    app.register_blueprint(help.bp)
    app.register_blueprint(login.bp)
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
    app.register_blueprint(murmur.bp, url_prefix='/settings/murmur')
    app.register_blueprint(permissions.bp, url_prefix='/settings/permissions')
    app.register_blueprint(permission.bp, url_prefix='/api/permission')
    app.register_blueprint(xup.bp, url_prefix='/xup')
    app.register_blueprint(ship_assignment.bp, url_prefix='/settings/ship_assignment')

    # notification
    app.register_blueprint(notification.bp, url_prefix="/notification")

def setup_coms():
    from waitlist.utility.coms import set_connector
    from waitlist.ts3.connection import TS3Connector
    from waitlist.utility.murmur.connector import MurmurConnector
    from waitlist.utility.settings import sget_active_coms_type
    com_type = sget_active_coms_type()
    if com_type is None:
        return
    if com_type == 'ts3':
        set_connector(TS3Connector())
    if com_type == 'murmur':
        set_connector(MurmurConnector())


logger = logging.getLogger(__name__)


def run_server():
    from waitlist.base import app
    from waitlist.utility import config
    from werkzeug.middleware.proxy_fix import ProxyFix
    from gevent.pywsgi import WSGIServer
    if config.proxy_enabled:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=config.proxy_for,
                                x_host=config.proxy_host,
                                x_proto=config.proxy_proto,
                                x_prefix=config.proxy_prefix)
    wsgi_logger = logging.getLogger("gevent.pywsgi.WSGIServer")
    server = WSGIServer((config.server_bind, config.server_port), app,
                        log=wsgi_logger, error_log=wsgi_logger)
    server.serve_forever()

def main():
    setup_logging()
    import argparse
    parser = argparse.ArgumentParser(description='Waitlist management')
    parser.add_argument('-c', '--create-config', action='store_true',
                        help='Creates a default config file, if there is \
                        no config file or adds missing config options to \
                        an existing one')

    arg_ns: argparse.Namespace = parser.parse_args()
    if arg_ns.create_config:
        # we need to import this to create the config template
        import waitlist.utility.config
        return

    register_blueprints()
    # connect account signal handler
    from waitlist.signal import handler
    handler.account.connect()

    handler.murmur.connect()

    handler.timetracking.connect()
    # we need to send the signal for first fleet
    # if there is one on startup
    from waitlist.base import db
    from waitlist.storage.database import CrestFleet
    from waitlist.signal import send_added_first_fleet
    if db.session.query(CrestFleet).count() > 0:
        f: CrestFleet = db.session.query(CrestFleet).first()
        send_added_first_fleet(main, f.fleetID)

    setup_coms()

    db.session.remove()

    run_server()

if __name__ == '__main__':
    main()
