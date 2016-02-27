from flask_login import LoginManager, login_user, login_required, current_user
from waitlist.storage import database
from flask.globals import request, current_app
import flask
from flask.app import Flask
from pprint import pprint
import logging
from waitlist.storage.database import Character, session, WaitlistEntry,\
    Waitlist
import cgi
from flask_principal import Principal, Identity, identity_changed, \
    identity_loaded, UserNeed, RoleNeed, Permission
from waitlist.permissions import WTMRoles
from flask.templating import render_template
import re
from waitlist import utils
from waitlist.storage.modules import resist_ships, logi_ships, sniper_ships,\
    dps_snips, sniper_weapons, dps_weapons, t3c_ships
from waitlist.utils import create_mod_map
from setup_wtm import WaitlistNames
from datetime import datetime
from flask.helpers import url_for
from werkzeug.utils import redirect


app = Flask(__name__)
app.secret_key = 'mcf4q37h0n59qc4307w98jd5fc723'
app.config['SESSION_TYPE'] = 'filesystem'

logger = app.logger

login_manager = LoginManager()
login_manager.init_app(app)
principals = Principal(app)

basichtml = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>How am I?</title>
  </head>
  <body style="background-color:lightgrey;">
    {0}
  </body>
</html>"""

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
            account = session.query(database.Account).filter(database.Account.id == current_user.id).first()
            for role in account.roles:
                logger.info("Add role %s", role.name)
                identity.provides.add(RoleNeed(role.name))


@app.route('/', methods=['GET'])
@login_required
def idx_site():
    return render_template("index.html")

@app.route("/xup", methods=['POST'])
def xup_submit():
    '''
    Parse the submited fitts
    Check which fits need additional Info
    Rattlesnake, Rokh, that other ugly thing Caldari BS lvl
    Basilisk, Scimitar Logi Lvl
    -> put info into comment of the fit
    '''
    fittings = request.form['fits']
    logilvl = int(request.form['logi'])
    caldari_bs_lvl = int(request.form['cbs'])
    
    # lets normalize linebreaks
    fittings = fittings.replace('[\n\r]+', "\n")
    
    # lets first find out what kind of fitting is used
    firstLine = re.split("\n+", fittings.strip(), maxsplit=1)[0]
    format_type = utils.get_fit_format(firstLine)
    
    fits = []
    
    if format_type == "eft":
        # split multiple fits
        eft_fits = re.split("\[.*,.*\]\n", fittings)
        for eft_fit in eft_fits:
            logger.info("Parsing fit")
            # just remove possible whitespace
            eft_fit = eft_fit.strip()
            parsed_fit = utils.parseEft(eft_fit)
            fits.append(parsed_fit)
    
    # TODO handle dna fits
    
    # detect, caldari resist ships + basi + scimi and add lvl comment
    # -- done --
    
    # find out if the user is already in a waitlist, if he is add him to more waitlist_entries according to his fits
    # or add more fits to his entries
    # else create new entries for him in all appropriate waitlist_entries
    # -- done --
    

    for fit in fits:
        if fit.ship_type in resist_ships:
            fit.comment += " <b>Caldari Battleship: " + str(caldari_bs_lvl)+"</b>"
        else:
            if fit.ship_type in logi_ships:
                fit.comment += " <b>Logistics Cruiser: " + str(logilvl)+"</b>"
    # get current users id
    
    eve_id = current_user.get_eve_id()
    
    # get the waitlist entries of this user
    waitlist_entries = session.query(WaitlistEntry).filter(WaitlistEntry.user == eve_id).all()
    
    dps = []
    sniper = []
    logi = []

    #query to check if sth is a weapon module
    '''
    SELECT count(1) FROM invtypes
    JOIN invmarketgroups AS weapongroup ON invtypes.marketGroupID = weapongroup.marketGroupID
    JOIN invmarketgroups AS wcat ON weapongroup.parentGroupID = wcat.marketGroupID
    JOIN invmarketgroups AS mcat ON wcat.parentGroupID = mcat.marketGroupID
    WHERE invtypes.typeName = ? AND mcat.parentGroupID = 10;/*10 == Turrets & Bays*/
    '''
    
    # split his fits into types for the different waitlist_entries
    for fit in fits:
        mod_map = create_mod_map(fit.modules)
        # check that ship is an allowed ship
        
        # it is a logi put on logi wl
        if fit.ship_type in logi_ships:
            logi.append(fit)
            continue;
        
        is_allowed = False
        if fit.ship_type in sniper_ships or fit.ship_type in dps_snips or fit.ship_type in t3c_ships:
            is_allowed = True
        
        if not is_allowed: # not an allowed ship, push it on dps list :P
            dps.append(fit)
            continue
        
        
        
        # filter out mods that don't exist at least 4 times
        # this way we avoid checking everything or choosing the wrong weapon on ships that have 7turrents + 1launcher
        possible_weapons = []
        for mod in mod_map:
            if mod_map[mod][1] >= 4:
                possible_weapons.append(mod)
        
        weapon_type = "None"
        for weapon in possible_weapons:
            if weapon in sniper_weapons:
                weapon_type = "sniper"
                break
            if weapon in dps_weapons:
                weapon_type = "dps"
                break
        
        # ships with no valid weapons put on dps wl
        if weapon_type == "None" or weapon_type == "dps":
            dps.append(fit)
            continue
        
        # ships with sniper weapons put on sniper wl
        if weapon_type == "sniper":
            sniper.append(fit)
            continue
    
    logi_entry = None
    sniper_entry = None
    dps_entry = None
    if len(waitlist_entries) > 0: # there are actually existing entries
        # if there are existing wl entries assign them to appropriate variables
        for wl in waitlist_entries:
            if wl.waitlist.name == WaitlistNames.logi:
                logi_entry = wl
                continue
            if wl.waitlist.name == WaitlistNames.dps:
                dps_entry = wl
                continue
            if wl.waitlist.name == WaitlistNames.sniper:
                sniper_entry = wl
                
    
    creationdt = datetime.now()
    
    add_entries_map = {}
    
    # we have a logi fit but no logi wl entry, so create one
    if len(logi) and logi_entry == None:
        logi_entry = WaitlistEntry()
        logi_entry.user = get_char_id()
        logi_entry.creation = creationdt # for sorting entries
        logi_entry.user = current_user.get_eve_id() # associate a user with the entry
        add_entries_map[WaitlistNames.logi] = logi_entry
    
    # same for dps
    if len(dps) and dps_entry == None:
        dps_entry = WaitlistEntry()
        dps_entry.user = get_char_id()
        dps_entry.creation = creationdt # for sorting entries
        dps_entry.user = current_user.get_eve_id() # associate a user with the entry
        add_entries_map[WaitlistNames.dps] = dps_entry

    # and sniper
    if len(sniper) and sniper_entry == None:
        sniper_entry = WaitlistEntry()
        sniper_entry.user = get_char_id()
        sniper_entry.creation = creationdt # for sorting entries
        sniper_entry.user = current_user.get_eve_id() # associate a user with the entry
        add_entries_map[WaitlistNames.sniper] = sniper_entry

    # iterate over sorted fits and add them to their entry
    for logifit in logi:
        logi_entry.fittings.append(logifit)
    
    for dpsfit in dps:
        dps_entry.fittings.append(dpsfit)
        
    for sniperfit in  sniper:
        sniper_entry.fittings.append(sniperfit)
        
    # now add the entries to the waitlist_entries
    
    waitlists = session.query(Waitlist).all()
    
    # add the new wl entries to the waitlists
    for wl in waitlists:
        if wl.name in add_entries_map:
            add_entries_map[wl.name].waitlist = wl
    
    return redirect(url_for('idx_site'))
        
@login_required
def get_char_id():
    current_user.get_eve_id()

@app.route("/xup", methods=['GET'])
@login_required
def xup_index():
    return render_template("xup.html")
    

admin_perm = Permission(RoleNeed(WTMRoles.admin.name))
@app.route('/need_admin')
@login_required
@admin_perm.require(http_exception=401)
def need_admin():
    return "Admin Needed here"

fc_perm = Permission(RoleNeed(WTMRoles.fc.name))
@app.route('/need_fc')
@login_required
@fc_perm.require(http_exception=401)
def need_fc():
    return "FC needed"

# callable like /tokenauth?token=359th8342rt0f3uwf0234r
@app.route('/tokenauth')
def login_fc():
    login_token = request.args.get('token');
    user = database.session.query(database.Account).filter(database.Account.login_token == login_token).first()

    # token was not found
    if user == None:
        return flask.abort(401);
    logger.info("Got User {0}", user)
    login_user(user);
    logger.info("Loged in User {0}", user)

    # notify principal extension
    identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))

    return basichtml.format(cgi.escape(current_user.__repr__()))

@login_manager.user_loader
def load_user(unicode_id):
    # it ia an account
    if unicode_id.startswith("acc"):
        unicode_id = unicode_id.replace("acc", "", 1)
        return get_account_from_db(int(unicode_id))
    
    if unicode_id.startswith("char"):
        unicode_id = unicode_id.replace("char", "", 1)
        return get_char_from_db(int(unicode_id))
    
    return None

@app.route("/admin/")
@login_required
def admin_base():
    return "Admin Page Here >.>"

# load an account by its id
def get_account_from_db(int_id):
    return database.session.query(database.Account).filter(database.Account.id == int_id).first()

# load a character by its id
def get_char_from_db(int_id):
    return database.session.query(database.Character).filter(database.Character.id == int_id).first()

def create_new_character(eve_id, char_name):
    char = Character(eve_id, char_name)
    database.session.add(char)
    return char

# @login_manager.request_loader
# def load_by_request(request):
#    pass

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
    
    is_igb = False
    
    # check for IGB
    user_agent = request.headers.get('User-Agent')
    if user_agent != None:
        is_igb = user_agent.find("EVE-IGB")

    # if we have a igb check if we are trusted!
    if is_igb:
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
    pprint(request.headers)
    if trused_header_value == TRUESTED_HEADER_YES:
        is_trusted = True
    #
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
    char = get_char_from_db(char_id);
    if char == None:
        # create a new char
        char_name = request.headers.get('Eve-Charname')
        char = create_new_character(char_id, char_name)
    login_user(char)
    logger.debug("Getting char id from headers succeeded.")
    return char.__repr__()

def unauth_igb_untrused():
    """
    Send message to enable trust
    """
    return "<html><head><script>CCPEVE.requestTrust(\"http://127.0.0.1:5000/\");</script></head><body><p>Please enable trust</p></body></html>"

def unauthorized_ogb():
    """
    Handle unauthorized users that visit with an out of game browser
    -> Redirect them to SSO
    """
    pass

if __name__ == '__main__':
    app.run()
