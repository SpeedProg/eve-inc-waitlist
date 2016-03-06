from flask.blueprints import Blueprint
import logging
from waitlist.data.perm import perm_remove_player, perm_management
from flask_login import login_required, current_user
from flask.globals import request
from waitlist.storage.database import WaitlistEntry, Shipfit, Waitlist
import re
from waitlist.storage.modules import resist_ships, logi_ships, dps_snips,\
    sniper_ships, t3c_ships, sniper_weapons, dps_weapons
from waitlist.data.names import WaitlistNames
from werkzeug.utils import redirect
from flask.helpers import url_for
from flask.templating import render_template
from datetime import datetime
from waitlist.utility.utils import get_fit_format, parseEft, create_mod_map,\
    get_char_id
from waitlist import db

bp_waitlist = Blueprint('bp_waitlist', __name__)
logger = logging.getLogger(__name__)


@bp_waitlist.route("/api/wl/remove/", methods=['POST'])
@login_required
@perm_remove_player.require(http_exception=401)
def wls_remove_player():
    playerId = request.form['playerId']
    if playerId == None:
        logger.error("Tried to remove player with None id from waitlists.")
    
    db.session.query(WaitlistEntry).filter(WaitlistEntry.user == int(playerId)).delete()
    db.session.commit()
    return "success"

# remove one of your fittings by id
@bp_waitlist.route("/api/self/fittings/remove/<int:fitid>")
@login_required
def remove_self_fit(fitid):
    fit = db.session.query(Shipfit).filter(Shipfit.id == fitid).first()
    db.session.delete(fit)
    wlentry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == fit.waitlist_id).first()
    if len(wlentry.fittings) <= 0:
        db.session.delete(wlentry)
    
    db.session.commit()
    return "success"

# remove your self from a wl by wl entry id
@bp_waitlist.route("/api/self/wlentry/remove/<int:entry_id>")
@login_required
def self_remove_wl_entry(entry_id):
    db.session.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).delete()
    return "success"


# remove your self from all wls
@bp_waitlist.route("/api/self/wl/remove")
@login_required
def self_remove_all():
    entries = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == current_user.get_char_id());
    for entry in entries:
        logger.info("Remove entry id=%d", entry.id)
        db.session.delete(entry)
    db.session.commit()
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
    
    logger.debug("Fittings to parse: %s", fittings)
    
    # lets normalize linebreaks
    fittings = fittings.replace("[\n\r]+", "\n")
    fittings = fittings.strip()
    
    # lets first find out what kind of fitting is used
    endLineIdx = fittings.find('\n')+1
    firstLine = fittings[:endLineIdx]
    format_type = get_fit_format(firstLine)
    
    fits = []
    
    # split fittings up in its fittings
    string_fits = []
    fitIter = re.finditer("\[.*,.*\]", fittings)
    sIdx = 0
    eIdx = 0
    firstIter = True
    for fitMatch in fitIter:
        if not firstIter:
            eIdx = fitMatch.start()-1
            string_fits.append(fittings[sIdx:eIdx].split('\n'))
        sIdx = fitMatch.start()

    string_fits.append(fittings[sIdx:].split('\n'))

        
    if format_type == "eft":        
        for fit in string_fits:
            parsed_fit = parseEft(fit)
            fits.append(parsed_fit)
    
    logger.info("Parsed %d fits", len(fits))
    # TODO handle dna fit

    for fit in fits:
        if fit.ship_type in resist_ships:
            if logilvl == 0:
                pass  # TODO ask for caldari bs lvl
            if fit.comment is None:
                fit.comment = "<b>Cal BS: " + str(caldari_bs_lvl) + "</b>"
            else:
                fit.comment += " <b>Cal BS: " + str(caldari_bs_lvl) + "</b>"
        else:
            if fit.ship_type in logi_ships:
                if logilvl == 0:
                    pass  # TODO ask for logi
                if fit.comment is None:
                    fit.comment = "<b>Logi: " + str(logilvl) + "</b>"
                else:
                    fit.comment += " <b>Logi: " + str(logilvl) + "</b>"
    # get current users id
    
    eve_id = current_user.get_eve_id()
    
    # get the waitlist entries of this user
    waitlist_entries = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == eve_id).all()
    
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
    
    waitlists = db.session.query(Waitlist).all()
    
    # add the new wl entries to the waitlists
    for wl in waitlists:
        if wl.name in add_entries_map:
            wl.entries.append(add_entries_map[wl.name])

    db.session.commit()
    return redirect(url_for('index'))
        


@bp_waitlist.route("/xup", methods=['GET'])
@login_required
def xup_index():
    return render_template("xup.html")


@bp_waitlist.route('/management')
@login_required
@perm_management.require(http_exception=401)
def management():
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
    
    
    return render_template("waitlist_management.html", lists=wlists)