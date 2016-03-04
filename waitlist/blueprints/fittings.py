from flask.blueprints import Blueprint
import logging
from waitlist.data.perm import perm_remove_player, perm_management, perm_admin,\
    perm_settings
from flask_login import login_required, current_user
from flask.globals import request
from waitlist.storage.database import session, WaitlistEntry, Shipfit, Waitlist
import re
from waitlist import utils
from waitlist.storage.modules import resist_ships, logi_ships, dps_snips,\
    sniper_ships, t3c_ships, sniper_weapons, dps_weapons
from waitlist.utils import create_mod_map, get_char_id
from waitlist.data.names import WaitlistNames
from werkzeug.utils import redirect
from flask.helpers import url_for
from flask.templating import render_template
from datetime import datetime

bp_waitlist = Blueprint('bp_waitlist', __name__, template_folder='templates')
logger = logging.getLogger(__name__)


@bp_waitlist.route("/api/wl/remove/", methods=['POST'])
@login_required
@perm_remove_player.require(http_exception=401)
def wls_remove_player():
    playerId = request.form['playerId']
    if playerId == None:
        logger.error("Tried to remove player with None id from waitlists.")
    
    session.query(WaitlistEntry).filter(WaitlistEntry.user == int(playerId)).delete(synchronize_session=False)
    session.commit()
    return "success"

# remove one of your fittings by id
@bp_waitlist.route("/api/self/fittings/remove/<int:fitid>")
@login_required
def remove_self_fit(fitid):
    fit = session.query(Shipfit).filter(Shipfit.id == fitid).first()
    session.delete(fit)
    wlentry = session.query(WaitlistEntry).filter(WaitlistEntry.id == fit.waitlist_id).first()
    if len(wlentry.fittings) <= 0:
        session.delete(wlentry)
    
    session.commit()
    return "success"

# remove your self from a wl by wl entry id
@bp_waitlist.route("/api/self/wlentry/remove/<int:entry_id>")
@login_required
def self_remove_wl_entry(entry_id):
    session.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).delete()
    return "success"


# remove your self from all wls
@bp_waitlist.route("/api/self/wl/remove")
@login_required
def self_remove_all():
    entries = session.query(WaitlistEntry).filter(WaitlistEntry.user == current_user.get_char_id());
    for entry in entries:
        logger.info("Remove entry id=%d", entry.id)
        session.delete(entry)
    session.commit()
    return "success";

@bp_waitlist.route("/xup", methods=['POST'])
@login_required
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
    
    logger.info("Parsed %d fits", len(fits))
    # TODO handle dna fits
    
    # detect, caldari resist ships + basi + scimi and add lvl comment
    # -- done --
    
    # find out if the user is already in a waitlist, if he is add him to more waitlist_entries according to his fits
    # or add more fits to his entries
    # else create new entries for him in all appropriate waitlist_entries
    # -- done --
    

    for fit in fits:
        if fit.ship_type in resist_ships:
            if logilvl == 0:
                pass  # TODO ask for caldari bs lvl
            if fit.comment is None:
                fit.comment = "<b>Caldari Battleship: " + str(caldari_bs_lvl) + "</b>"
            else:
                fit.comment += " <b>Caldari Battleship: " + str(caldari_bs_lvl) + "</b>"
        else:
            if fit.ship_type in logi_ships:
                if logilvl == 0:
                    pass  # TODO ask for logi
                if fit.comment is None:
                    fit.comment = "<b>Logistics Cruiser: " + str(logilvl) + "</b>"
                else:
                    fit.comment += " <b>Logistics Cruiser: " + str(logilvl) + "</b>"
    # get current users id
    
    eve_id = current_user.get_eve_id()
    
    # get the waitlist entries of this user
    waitlist_entries = session.query(WaitlistEntry).filter(WaitlistEntry.user == eve_id).all()
    
    dps = []
    sniper = []
    logi = []

    # query to check if sth is a weapon module
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
        
        if not is_allowed:  # not an allowed ship, push it on dps list :P
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
    if len(waitlist_entries) > 0:  # there are actually existing entries
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
        logi_entry.creation = creationdt  # for sorting entries
        logi_entry.user = current_user.get_eve_id()  # associate a user with the entry
        add_entries_map[WaitlistNames.logi] = logi_entry
    
    # same for dps
    if len(dps) and dps_entry == None:
        dps_entry = WaitlistEntry()
        dps_entry.user = get_char_id()
        dps_entry.creation = creationdt  # for sorting entries
        dps_entry.user = current_user.get_eve_id()  # associate a user with the entry
        add_entries_map[WaitlistNames.dps] = dps_entry

    # and sniper
    if len(sniper) and sniper_entry == None:
        sniper_entry = WaitlistEntry()
        sniper_entry.user = get_char_id()
        sniper_entry.creation = creationdt  # for sorting entries
        sniper_entry.user = current_user.get_eve_id()  # associate a user with the entry
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
            wl.entries.append(add_entries_map[wl.name])

    session.commit()
    return redirect(url_for('index'))
        


@bp_waitlist.route("/xup", methods=['GET'])
@login_required
def xup_index():
    return render_template("xup.html", perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management)


@bp_waitlist.route('/management')
@login_required
@perm_management.require(http_exception=401)
def management():
    all_waitlists = session.query(Waitlist).all();
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
    
    
    return render_template("waitlist_management.html", lists=wlists, perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management)