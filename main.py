# inject the lib folder before everything else
import os
import sys
from waitlist.blueprints.feedback import feedback
from waitlist.data.eve_xml_api import get_char_info_for_character,\
    get_corp_info_for_corporation
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))

from waitlist import app, login_manager, db
from flask_login import login_required, current_user, login_user,\
    logout_user
import logging
from waitlist.storage.database import Waitlist, Account
from flask_principal import RoleNeed, identity_changed, Identity, AnonymousIdentity,\
    identity_loaded, UserNeed
from waitlist.data.perm import perm_management, perm_settings, perm_admin,\
    perm_officer
from flask.templating import render_template
from waitlist.blueprints.settings import bp_settings
from waitlist.blueprints.fittings import bp_waitlist
from flask.globals import request, current_app
import flask
from werkzeug.utils import redirect
from flask.helpers import url_for
from waitlist.data.names import WaitlistNames
from waitlist.utility.utils import is_igb, get_account_from_db, get_char_from_db,\
    get_character_by_id_and_name, is_corp_banned, is_alliance_banned,\
    is_char_banned

app.register_blueprint(bp_waitlist)
app.register_blueprint(bp_settings, url_prefix='/settings')
app.register_blueprint(feedback, url_prefix="/feedback")

logger = logging.getLogger(__name__)

# set if it is the igb
@app.context_processor
def inject_data():
    return dict(is_igb=is_igb(), perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management, perm_officer=perm_officer)

@app.before_request
def check_ban():
    if current_user.is_authenticated:
        if current_user.type == "character":
            if is_char_banned(current_user):
                logout_user()
                for key in ('identity.name', 'identity.auth_type'):
                    flask.globals.session.pop(key, None)
            
                # Tell Flask-Principal the user is anonymous
                identity_changed.send(current_app._get_current_object(),
                                      identity=AnonymousIdentity())
                    
    

@app.route('/', methods=['GET'])
@login_required
def index():
    all_waitlists = db.session.query(Waitlist).all();
    wlists = []
    logi_wl = None
    dps_wl = None
    sniper_wl = None

    for wl in all_waitlists:
        if wl.name == WaitlistNames.logi:
            logi_wl = wl
            continue
        if wl.name == WaitlistNames.dps:
            dps_wl = wl
            continue
        if wl.name == WaitlistNames.sniper:
            sniper_wl = wl
            continue
    wlists.append(logi_wl)
    wlists.append(dps_wl)
    wlists.append(sniper_wl)
    
    return render_template("index.html", lists=wlists, user=current_user)


@login_manager.user_loader
def load_user(unicode_id):
    # it is an account
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
    logger.info("Got User %s", user)
    login_user(user);
    logger.info("Logged in User %s", user)

    # notify principal extension
    identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))

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
        
    if is_char_banned(char):
        return flask.abort(401, 'You are banned!')

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




if __name__ == '__main__':
    logger = app.logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    waitlistlogger = logging.getLogger("waitlist")
    waitlistlogger.addHandler(ch)
    waitlistlogger.setLevel(logging.INFO)
    app.run(host="0.0.0.0", port=81, debug=False)
