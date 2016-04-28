from gevent import monkey; monkey.patch_all()
# inject the lib folder before everything else
import os
import sys
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist.data.version import version
from waitlist.utility.eve_id_utils import get_account_from_db, get_char_from_db,\
    is_char_banned, get_character_by_id_and_name, get_character_by_name
from datetime import datetime
import math
from waitlist.blueprints.waitlist_api import wl_api
from sqlalchemy.exc import StatementError
from waitlist.utility import config
from logging.handlers import TimedRotatingFileHandler
from waitlist.blueprints.feedback import feedback
from gevent.pywsgi import WSGIServer
from waitlist import app, login_manager, db
from flask_login import login_required, current_user, login_user,\
    logout_user
import logging
from waitlist.storage.database import Account, WaitlistEntry,\
    Character, WaitlistGroup
from flask_principal import RoleNeed, identity_changed, Identity, AnonymousIdentity,\
    identity_loaded, UserNeed
from waitlist.data.perm import perm_management, perm_settings, perm_admin,\
    perm_officer, perm_accounts, perm_feedback, perm_dev, perm_leadership,\
    perm_bans, perm_viewfits, perm_comphistory
from flask.templating import render_template
from waitlist.blueprints.settings import bp_settings
from waitlist.blueprints.fittings import bp_waitlist
from flask.globals import request, current_app
import flask
from werkzeug.utils import redirect
from flask.helpers import url_for
from waitlist.utility.utils import is_igb

app.register_blueprint(bp_waitlist)
app.register_blueprint(bp_settings, url_prefix='/settings')
app.register_blueprint(feedback, url_prefix="/feedback")
app.register_blueprint(wl_api, url_prefix="/wl_api")

logger = logging.getLogger(__name__)

# set if it is the igb
@app.context_processor
def inject_data():
    is_account = False
    if hasattr(current_user, 'type'):
        is_account=(current_user.type == "account")

    return dict(is_igb=is_igb(), perm_admin=perm_admin,
                perm_settings=perm_settings, perm_man=perm_management,
                perm_officer=perm_officer, perm_accounts=perm_accounts,
                perm_feedback=perm_feedback, is_account=is_account,
                perm_dev=perm_dev, perm_leadership=perm_leadership, perm_bans=perm_bans,
                perm_viewfits=perm_viewfits, version=version, perm_comphistory=perm_comphistory)

@app.before_request
def check_ban():
    if current_user.is_authenticated:
        if current_user.type == "character":
            is_banned, _ = is_char_banned(current_user)
            if is_banned:
                force_logout()
            else:
                # check if character has right charid in header, since clients seem to share ids
                # this could be used to detect multiboxers actually
                if is_igb(): # should allways be if he is char authenticated, but well lets check again
                    char_id_str = request.headers.get('Eve-Charid')
                    if char_id_str is None: # he was logged in with other account and no trust on this
                        force_logout()
                        return
                    char_id = int(char_id_str)
                    if current_user.get_eve_id() != char_id:
                        force_logout()
        elif current_user.type == "account":
            if current_user.disabled:
                force_logout()
            

def force_logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        flask.globals.session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

@app.route('/', methods=['GET'])
@login_required
def index():
    if 'groupId' in request.args:
        group_id = int(request.args.get('groupId'))
        group = db.session.query(WaitlistGroup).get(group_id)
    else:
        group = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True).order_by(WaitlistGroup.odering).first()
    
    if group == None:
        return render_template("index.html", is_index=True)
    
    new_bro = True
    if current_user.type == "character":
        if current_user.newbro == None:
            new_bro = True
        else:
            new_bro = current_user.newbro
    elif current_user.type == "account":
        if current_user.current_char_obj.newbro == None:
            new_bro = True
        else:
            new_bro = current_user.current_char_obj.newbro
    
    wlists = []
    logi_wl = group.logilist
    dps_wl = group.dpslist
    sniper_wl = group.sniperlist
    queue = group.xuplist
    other_wl = group.otherlist

    wlists.append(queue)
    wlists.append(logi_wl)
    wlists.append(dps_wl)
    wlists.append(sniper_wl)
    if (other_wl is not None):
        wlists.append(other_wl)
    
    activegroups = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True).all()
    
    return render_template("index.html", lists=wlists, user=current_user, is_index=True, is_on_wl=is_on_wl(), newbro=new_bro, group=group, groups=activegroups)

def is_on_wl():
    eveId = current_user.get_eve_id();
    entry = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == eveId).first();
    return (entry is not None)

@app.route("/help", methods=["GET"])
def site_help():
    return render_template("help.html")

@login_manager.user_loader
def load_user(unicode_id):
    # it is an account
    try:
        return get_user_from_db(unicode_id)
    except StatementError:
        db.session.rollback()
        logger.exception("Failed to get user from db")
        return get_user_from_db(unicode_id)

def get_user_from_db(unicode_id):
    if unicode_id.startswith("acc"):
        unicode_id = unicode_id.replace("acc", "", 1)
        return get_account_from_db(int(unicode_id))
    
    if unicode_id.startswith("char"):
        unicode_id = unicode_id.replace("char", "", 1)
        return get_char_from_db(int(unicode_id))
    
    return None

# callable like /tokenauth?token=359th8342rt0f3uwf0234r
@app.route('/tokenauth')
def login_token():
    login_token = request.args.get('token');
    user = db.session.query(Account).filter(Account.login_token == login_token).first()

    # token was not found
    if user == None:
        return flask.abort(401);
    
    if user.disabled:
        return flask.abort(403)
    
    logger.info("Got User %s", user)
    login_user(user);
    logger.info("Logged in User %s", user)

    # notify principal extension
    identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))

    return redirect(url_for('index'), code=303)

@app.route("/charauth")
def char_auth():
    token = request.args.get('token')
    logger.info("Token %s", token)
    character = db.session.query(Character).filter(Character.login_token == token).first()
    # token was not found
    if character == None:
        return flask.abort(401);
    logger.info("Got User %s", character)
    login_user(character);
    logger.info("Logged in User %s", character)

    # notify principal extension
    identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(character.id))

    return redirect(url_for('index'), code=303)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    
    for key in ('identity.name', 'identity.auth_type'):
        flask.globals.session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return render_template("logout.html")

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user
    # Add the UserNeed to the identity
    logger.info("loading identity for %s", current_user)
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))


    if hasattr(current_user, "type"):  # it is a custom user class
        if current_user.type == "account":  # it is an account, so it can have roles
            account = db.session.query(Account).filter(Account.id == current_user.id).first()
            for role in account.roles:
                logger.info("Add role %s", role.name)
                identity.provides.add(RoleNeed(role.name))

@login_manager.unauthorized_handler
def unauthorized():
    '''
    FC should have a login token, that always going stay the same
    additionally they are going to have login form
    
    if we have igb headers,
        if the user has no roles or only one of the flowing:
            log them in by header
        else
            Redirect them to SSO login
    else:
        Redirect to SSO login
        // here the user has the ability to activate trust and get logged in on the next request by headers
        then check them and try to log the user in
        ONLY users with no roles ore the following '' are allowed to login by headers
       
    TODO: Implement 
    '''

    # if we have a igb check if we are trusted!
    if is_igb():
        return unauthorized_igb()
    
    return unauthorized_ogb()

def unauthorized_igb():
    """
    Handle unauthroized users that visit from the ingame browser
    """
    TRUSTED_HEADER = "Eve-Trusted"
    # TRUESTED_HEADER_NO = "No"
    TRUESTED_HEADER_YES = "Yes"
    
    is_trusted = False
    trused_header_value = request.headers.get(TRUSTED_HEADER)

    if trused_header_value == TRUESTED_HEADER_YES:
        is_trusted = True

    if (is_trusted):
        return unauth_igb_trusted()
    
    return unauth_igb_untrused()

def unauth_igb_trusted():
    """
    Handle users with igb that trusted us
    -> try to authorize them by headers, if they are not restricted
    """
    char_id_str = request.headers.get('Eve-Charid')
    if char_id_str == None:
        logger.debug("Getting char id from headers failed")
        return flask.abort(400)

    char_id = int(char_id_str)
    char_name = request.headers.get('Eve-Charname')
    char = get_character_by_id_and_name(char_id, char_name)
    is_banned, reason = is_char_banned(char)
    if is_banned:
        return flask.abort(401, 'You are banned, because your '+reason+" is banned!")

    login_user(char, remember=True)
    logger.debug("Getting char id from headers succeeded.")
    return redirect(url_for("index"))

def unauth_igb_untrused():
    """
    Send message to enable trust
    """
    return render_template("enable_trust.html")

def unauthorized_ogb():
    """
    Handle unauthorized users that visit with an out of game browser
    -> Redirect them to SSO
    """
    return "Login Without Token not yet available"

@app.route("/update_token")
@login_required
@perm_admin.require(http_exception=401)
def create_char_logintoken():
    username = request.args.get('char')
    print username
    eve_char = get_character_by_name(username)
    token = eve_char.get_login_token()
    db.session.commit()
    return token

@app.template_filter('waittime')
def jinja2_waittime_filter(value):
    currentUTC = datetime.utcnow()
    waitedTime = currentUTC-value
    return str(int(math.floor(waitedTime.total_seconds()/60)))

if __name__ == '__main__':
    err_fh = TimedRotatingFileHandler(filename=config.error_log, when="midnight", interval=1, utc=True)
    info_fh = TimedRotatingFileHandler(filename=config.info_log, when="midnight", interval=1, utc=True)
    access_fh = TimedRotatingFileHandler(filename=config.access_log, when="midnight", interval=1, utc=True)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    err_fh.setFormatter(formatter)
    info_fh.setFormatter(formatter)
    access_fh.setFormatter(formatter)

    info_fh.setLevel(logging.INFO)
    err_fh.setLevel(logging.ERROR)

    waitlistlogger = logging.getLogger("waitlist")
    waitlistlogger.addHandler(err_fh)
    waitlistlogger.addHandler(info_fh)
    waitlistlogger.setLevel(logging.INFO)

    app.logger.addHandler(err_fh)
    app.logger.addHandler(info_fh)
    app.logger.setLevel(logging.INFO)
    
    wsgi_logger = logging.getLogger("gevent.pywsgi.WSGIServer")
    wsgi_logger.addHandler(err_fh)
    wsgi_logger.addHandler(access_fh)
    wsgi_logger.setLevel(logging.INFO)
    #app.run(host="0.0.0.0", port=81, debug=True)
    server = WSGIServer((config.server_bind, config.server_port), app, log=wsgi_logger, error_log=wsgi_logger)
    server.serve_forever()
