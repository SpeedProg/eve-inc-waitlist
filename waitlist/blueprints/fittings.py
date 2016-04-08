from flask.blueprints import Blueprint
import logging
from waitlist.data.perm import perm_management, perm_dev
from flask_login import login_required, current_user
from flask.globals import request
from waitlist.storage.database import WaitlistEntry, Shipfit, Waitlist,\
    Character, InvType, MarketGroup, HistoryEntry
import re
from waitlist.storage.modules import resist_ships, logi_ships,\
    sniper_ships, t3c_ships, sniper_weapons, dps_weapons, dps_ships,\
    weapongroups
from waitlist.data.names import WaitlistNames
from werkzeug.utils import redirect
from flask.helpers import url_for, flash
from flask.templating import render_template
from datetime import datetime, timedelta
from waitlist.utility.utils import get_fit_format, parseEft, create_mod_map,\
    get_character
from waitlist import db
from waitlist.blueprints import send_invite_notice, subscriptions
from waitlist.data.sse import ServerSentEvent, InviteEvent
from flask import Response
from gevent.queue import Queue
from waitlist.blueprints.fleetstatus import fleet_status
import flask
from sqlalchemy.sql.expression import desc


def create_history_object(targetID, event_type, sourceID=None, fitlist=None):
    hEntry = HistoryEntry()
    hEntry.sourceID = sourceID
    hEntry.targetID = current_user.get_eve_id()
    hEntry.action = event_type
    if fitlist is not None:
        for fit in fitlist:
            hEntry.fittings.append(fit)
    return hEntry

bp_waitlist = Blueprint('fittings', __name__)
logger = logging.getLogger(__name__)


@bp_waitlist.route("/api/wl/remove/", methods=['POST'])
@login_required
@perm_management.require(http_exception=401)
def api_wls_remove_player():
    playerId = int(request.form['playerId'])
    if playerId == None:
        logger.error("Tried to remove player with None id from waitlists.")
    
    # don't remove from queue
    queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first()
    waitlist_entries = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == playerId) & (WaitlistEntry.waitlist_id != queue.id)).all()
    fittings = []
    for entry in waitlist_entries:
        fittings.extend(entry.fittings)
    
    db.session.query(WaitlistEntry).filter((WaitlistEntry.user == playerId) & (WaitlistEntry.waitlist_id != queue.id)).delete()
    hEntry = create_history_object(playerId, HistoryEntry.EVENT_COMP_RM_PL, current_user.id, fittings)
    db.session.add(hEntry)
    db.session.commit()
    character = db.session.query(Character).filter(Character.id == playerId).first()
    logger.info("%s removed %s from waitlist.", current_user.username, character.eve_name)

    return "OK"

@bp_waitlist.route("/api/wl/invite", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def api_invite_player():
    playerId = int(request.form['playerId'])
    if playerId == None:
        logger.error("Tried to remove player with None id from waitlists.")
    
    # don't remove from queue
    #queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first()
    
    #db.session.query(WaitlistEntry).filter((WaitlistEntry.user == playerId) & (WaitlistEntry.waitlist_id != queue.id)).delete()
    #db.session.commit()
    event = InviteEvent(playerId)
    send_invite_notice(event)
    #publish(event)
    character = db.session.query(Character).filter(Character.id == playerId).first()
    hEntry = create_history_object(character.get_eve_id(), HistoryEntry.EVENT_COMP_INV_PL, current_user.id)
    db.session.add(hEntry)
    db.session.commit()
    logger.info("%s invited %s to fleet.", current_user.username, character.eve_name)
    return "OK"

@bp_waitlist.route("/api/wl/entries/remove/", methods=['POST'])
@login_required
@perm_management.require(http_exception=401)
def api_wl_remove_entry():
    entryId = int(request.form['entryId'])
    entry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == entryId).first()
    hEntry = create_history_object(entry.user_data.get_eve_id(), HistoryEntry.EVENT_COM_RM_ETR, current_user.id, entry.fittings)
    db.session.add(hEntry)
    logger.info("%s removed %s from waitlist %s", current_user.username, entry.user_data.get_eve_name(), entry.waitlist.name)
    db.session.query(WaitlistEntry).filter(WaitlistEntry.id == entryId).delete()
    db.session.commit()
    return "OK"

# remove one of your fittings by id
@bp_waitlist.route("/api/self/fittings/remove/<int:fitid>", methods=["DELETE"])
@login_required
def remove_self_fit(fitid):
    logger.info("%s removed their fit with id %d", current_user.get_eve_name(), fitid)
    fit = db.session.query(Shipfit).filter(Shipfit.id == fitid).first()
    wlentry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == fit.waitlist.id).first()
    
    if (wlentry.user == current_user.get_eve_id()):
        wlentry.fittings.remove(fit)
        # don't delete anymore we need them for history
        #db.session.delete(fit)
        if len(wlentry.fittings) <= 0:
            db.session.delete(wlentry)
        hEntry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_SELF_RM_FIT, None, [fit])
        db.session.add(hEntry)
        db.session.commit()
    else:
        flask.abort(403)

    return "success"

# remove your self from a wl by wl entry id
@bp_waitlist.route("/api/self/wlentry/remove/<int:entry_id>", methods=["DELETE"])
@login_required
def self_remove_wl_entry(entry_id):
    logger.info("%s removed their own entry with id %d", current_user.get_eve_name(), entry_id)
    entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.id == entry_id) & (WaitlistEntry.user == current_user.get_eve_id())).first()
    hEntry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_SELF_RM_ETR, None, entry.fittings)
    db.session.add(hEntry)
    db.session.delete(entry)
    db.session.commit()
    return "success"


# remove your self from all wls
@bp_waitlist.route("/api/self/wl/remove", methods=["DELETE"])
@login_required
def self_remove_all():
    logger.info("%s removed them selfs from waitlists", current_user.get_eve_name())
    #queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first()
    # remove from all lists except queue
    entries = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == current_user.get_eve_id());
    fittings = []
    for entry in entries:
        fittings.extend(entry.fittings)
    
    hEntry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_SELF_RM_WLS_ALL, None, fittings)
    db.session.add(hEntry)

    for entry in entries:
        logger.info("%s removed own entry with id=%s", current_user.get_eve_name(), entry.id)
        db.session.delete(entry)

    db.session.commit()
    return "success";

@bp_waitlist.route("/xup", methods=['POST'])
@login_required
def xup_submit():
    if not fleet_status.xup_enabled:
        # xups are disabled atm
        flash("X-UP is disabled!!!")
        return redirect(url_for("index"))
    '''
    Parse the submited fitts
    Check which fits need additional Info
    Rattlesnake, Rokh, that other ugly thing Caldari BS lvl
    Basilisk, Scimitar Logi Lvl
    -> put info into comment of the fit
    '''
    fittings = request.form['fits']
    eve_id = current_user.get_eve_id()
    # check if it is scruffy
    if fittings.lower().startswith("scruffy"):
        # scruffy mode scruffy
        fittings = fittings.lower()
        _, _, ship_type = fittings.rpartition(" ")
        shipTypes = []
        # check for , to see if it is a multi value shiptype
        if "," in ship_type:
            for stype in ship_type.split(","):
                stype = stype.strip()
                if stype == WaitlistNames.logi or stype == WaitlistNames.dps or stype == WaitlistNames.sniper:
                    shipTypes.append(stype)
        else:
            if ship_type == WaitlistNames.logi or ship_type == WaitlistNames.dps or ship_type == WaitlistNames.sniper:
                shipTypes.append(ship_type)

        # check if shiptype is valid
        if len(shipTypes) <= 0:
            flash("Valid entries are scruffy [dps|logi|sniper,..]")
            return redirect(url_for('index'))

        queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first();
        wl_entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.waitlist_id == queue.id) & (WaitlistEntry.user == eve_id)).first()
        if wl_entry is None:
            wl_entry = WaitlistEntry()
            wl_entry.creation = datetime.utcnow()
            wl_entry.user = eve_id
            queue.entries.append(wl_entry)
        
        hEntry = create_history_object(current_user.get_eve_id(), "xup")
        
        for stype in shipTypes:
            fit = Shipfit()
            fit.ship_type = 1##System >.>
            fit.wl_type = stype
            
            wl_entry.fittings.append(fit)
            hEntry.fittings.append(fit)
        
        db.session.add(hEntry)
        
        db.session.commit()
        
        flash("You where added as "+ship_type)
        
        return redirect(url_for('index'))
        
        
    logilvl = request.form['logi']
    if logilvl == "":
        logilvl = "0"
    caldari_bs_lvl = request.form['cbs']
    if caldari_bs_lvl == "":
        caldari_bs_lvl = "0"
    logilvl = int(logilvl)
    caldari_bs_lvl = int(caldari_bs_lvl)
    newbro = request.form.get('newbro', "off")
    newbro = (newbro is not "off")
    get_character(current_user).newbro = newbro
    
    current_user.cbs_level = caldari_bs_lvl
    current_user.lc_level = logilvl
    
    logger.debug("Fittings to parse: %s", fittings)
    
    # lets normalize linebreaks
    fittings = fittings.replace("[\n\r]+", "\n")
    fittings = fittings.strip()
    
    # lets first find out what kind of fitting is used
    endLineIdx = fittings.find('\n')+1
    firstLine = fittings[:endLineIdx]
    format_type = get_fit_format(firstLine)
    
    fits = []
    if format_type == "eft":
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
            else:
                firstIter = False
               
            sIdx = fitMatch.start()
    
        string_fits.append(fittings[sIdx:].split('\n'))
    
        logger.debug("Split fittings into %d fits", len(string_fits))
        
    
        for fit in string_fits:
            parsed_fit = parseEft(fit)
            fits.append(parsed_fit)
    
    else:
        # parse chat links
        # [17:41:27] Anami Sensi > x  <url=fitting:11978:14240;3:31366;1:31952;1:17528;3:31378;1:3608;4:12058;1:4348;1:33706;5:23711;4:29001;3:29011;1:28668;426::>Guardian4Life</url>
        # [18:02:07] Bruce Warhead > x  <url=fitting:17740:2048;1:26076;1:17559;1:3186;8:33844;2:19317;1:15895;4:26394;1:14268;1:4349;2:2446;5:29001;1:12787;4888:12791;7368::>VeniVindiVG</url> sdf3>yx <url=fitting:11978:14240;3:1987;1:1447;1:31378;2:14134;2:3608;4:12058;1:4349;1:33706;4:23711;5:29001;3:28668;97::>&gt;.&gt;</url>
        lines = fittings.split('\n')
        for line in lines:
            fitIter = re.finditer("<url=fitting:(\d+):([\d;:]+)>", line)
            for fitMatch in fitIter:
                ship_type = int(fitMatch.group(1))
                dna_fit = fitMatch.group(2)
                fit = Shipfit()
                fit.ship_type = ship_type
                fit.modules = dna_fit
                fits.append(fit)            
        
    fit_count = len(fits)
    
    logger.debug("Parsed %d fits", fit_count)
    
    if fit_count <= 0:
        flash("You submitted {0} fits to be check by a fleet comp before getting on the waitlist.".format(fit_count), "danger")
        return redirect(url_for('index'))

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
                comment_string = ""
                
                if logilvl <= 3:
                    comment_string = "<b class=\"bg-danger\">Logi: {0}</b>"
                else:
                    comment_string = "<b>Logi: {0}</b>"

                if fit.comment is None:
                    fit.comment = comment_string.format(logilvl)
                else:
                    fit.comment += " " + comment_string.format(logilvl)
    # get current users id
    
    eve_id = current_user.get_eve_id()

    # query to check if sth is a weapon module
    '''
    SELECT count(1) FROM invtypes
    JOIN invmarketgroups AS weapongroup ON invtypes.marketGroupID = weapongroup.marketGroupID
    JOIN invmarketgroups AS wcat ON weapongroup.parentGroupID = wcat.marketGroupID
    JOIN invmarketgroups AS mcat ON wcat.parentGroupID = mcat.marketGroupID
    WHERE invtypes.typeName = ? AND mcat.parentGroupID = 10;/*10 == Turrets & Bays*/
    '''
    
    fits_ready = []
    
    # split his fits into types for the different waitlist_entries
    for fit in fits:
        mod_map = create_mod_map(fit.modules)
        # check that ship is an allowed ship
        
        # it is a logi put on logi wl
        if fit.ship_type in logi_ships:
            fit.wl_type = WaitlistNames.logi
            fits_ready.append(fit)
            continue;
        
        is_allowed = False
        if fit.ship_type in sniper_ships or fit.ship_type in dps_ships or fit.ship_type in t3c_ships:
            is_allowed = True
        
        if not is_allowed:  # not an allowed ship, push it on dps list :P
            fit.wl_type = WaitlistNames.dps
            fits_ready.append(fit)
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
                weapon_type = WaitlistNames.sniper
                break
            if weapon in dps_weapons:
                weapon_type = WaitlistNames.dps
                break
        
        if weapon_type == "None":
            # try to decide by market group
            for weapon in possible_weapons:
                weapon_db = db.session.query(InvType).filter(InvType.typeID == weapon).first()
                if weapon_db is None:
                    continue
                market_group = db.session.query(MarketGroup).filter(MarketGroup.marketGroupID == weapon_db.marketGroupID).first()
                if market_group is None:
                    continue
                parent_group = db.session.query(MarketGroup).filter(MarketGroup.marketGroupID == market_group.parentGroupID).first()
                if parent_group is None:
                    continue
                
                # we have a parent market group
                if parent_group.marketGroupName in weapongroups['dps']:
                    weapon_type = WaitlistNames.dps
                    break
                if parent_group.marketGroupName in weapongroups['sniper']:
                    weapon_type = WaitlistNames.sniper
                    break    
        
        # ships with no valid weapons put on dps wl
        if weapon_type == "None" or weapon_type == WaitlistNames.dps:
            fit.wl_type = WaitlistNames.dps
            fits_ready.append(fit)
            continue
        
        # ships with sniper weapons put on sniper wl
        if weapon_type == WaitlistNames.sniper:
            fit.wl_type = WaitlistNames.sniper
            fits_ready.append(fit)
            continue

    """
    #this stuff is needed somewhere else now
    # get the waitlist entries of this user

    """
    queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first();
    wl_entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.waitlist_id == queue.id) & (WaitlistEntry.user == eve_id)).first()
    if wl_entry is None:
        wl_entry = WaitlistEntry()
        wl_entry.creation = datetime.utcnow()
        wl_entry.user = eve_id
        queue.entries.append(wl_entry)
    
    
    logger.info("%s submitted %s fits to be checked by a fleetcomp", current_user.get_eve_name(), len(fits_ready))
    
    for fit in fits_ready:
        logger.info("%s submits %s", current_user.get_eve_name(), fit.get_dna())
        wl_entry.fittings.append(fit)
    
    hEntry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_XUP, None, fits_ready)
    
    db.session.add(hEntry)
    db.session.commit()
    
    flash("You submitted {0} fits to be check by a fleet comp before getting on the waitlist.".format(fit_count), "success")
    
    return redirect(url_for('index'))
        

@bp_waitlist.route("/move_to_waitlist", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def move_to_waitlists():
    entry_id = int(request.form['entryId'])
    fit_ids = request.form['fitIds']
    fitIds = [int(x) for x in fit_ids.split(",")]
    entry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).first()
    if entry == None:
        return "OK";
    logger.info("%s approved %s", current_user.username, entry.user_data.get_eve_name())
    waitlist_entries = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == entry.user).all()
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
    
    # sort fittings by ship type
    logi = []
    dps = []
    sniper = []
    hEntry = create_history_object(entry.user, HistoryEntry.EVENT_COMP_MV_XUP_ETR, current_user.id)
    for fit in entry.fittings:
        if not fit.id in fitIds:
            continue
        hEntry.fittings.append(fit)
    
    fits_to_remove = []
    
    for fit in entry.fittings:
        if not fit.id in fitIds:
            logger.info("Skipping %s because not in %s", fit, fit_ids)
            continue
        logger.info("Sorting fit %s by type into %s", str(fit), fit.wl_type)
        
        if fit.wl_type == WaitlistNames.logi:
            logi.append(fit)
        elif fit.wl_type == WaitlistNames.dps:
            dps.append(fit)
        elif fit.wl_type == WaitlistNames.sniper:
            sniper.append(fit)
        else:
            logger.error("Failed to add %s do a waitlist.", fit)

        fits_to_remove.append(fit)
    
    for fit in fits_to_remove:
        entry.fittings.remove(fit)
    
    add_entries_map = {}
    
    # we have a logi fit but no logi wl entry, so create one
    if len(logi) and logi_entry == None:
        logi_entry = WaitlistEntry()
        logi_entry.creation = entry.creation  # for sorting entries
        logi_entry.user = entry.user  # associate a user with the entry
        add_entries_map[WaitlistNames.logi] = logi_entry
    
    # same for dps
    if len(dps) and dps_entry == None:
        dps_entry = WaitlistEntry()
        dps_entry.creation = entry.creation  # for sorting entries
        dps_entry.user = entry.user  # associate a user with the entry
        add_entries_map[WaitlistNames.dps] = dps_entry

    # and sniper
    if len(sniper) and sniper_entry == None:
        sniper_entry = WaitlistEntry()
        sniper_entry.creation = entry.creation  # for sorting entries
        sniper_entry.user = entry.user  # associate a user with the entry
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
    
    # add history entry to db
    db.session.add(hEntry)

    db.session.commit()
    if (len(entry.fittings) <= 0):
        db.session.delete(entry)
    db.session.commit()
    
    return "OK"
    

@bp_waitlist.route("/move_fit_to_waitlist", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def api_move_fit_to_waitlist():
    fit_id = int(request.form['fit_id'])
    fit = db.session.query(Shipfit).filter(Shipfit.id == fit_id).first();
    if fit == None: # fit doesn't exist, probably double trigger when moving some one
        return "OK"
    entry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == fit.waitlist.id).first();
    
    logger.info("%s approved fit %s from %s", current_user.username, fit, entry.user_data.get_eve_name())
    
    # get the entry for the wl we need
    wl_entry = db.session.query(WaitlistEntry).join(Waitlist).filter((WaitlistEntry.user == entry.user) & (Waitlist.name == fit.wl_type)).first();
    new_entry = False
    # if it doesn't exist create it
    if wl_entry == None:
        wl_entry = WaitlistEntry()
        wl_entry.creation = entry.creation
        wl_entry.user = entry.user
        new_entry = True
    
    #remove fit from old entry
    entry.fittings.remove(fit)
    #add the fit to the entry
    wl_entry.fittings.append(fit)
    
    # add a history entry
    hEntry = create_history_object(entry.user, HistoryEntry.EVENT_COMP_MV_XUP_FIT, current_user.id, [fit])
    db.session.add(hEntry)
    
    if new_entry:
        waitlist = db.session.query(Waitlist).filter(Waitlist.name == fit.wl_type).first();
        waitlist.entries.append(wl_entry)
    
    db.session.commit()
    if (len(entry.fittings) == 0):
        db.session.delete(entry)
        db.session.commit()
    
    return "OK"

@bp_waitlist.route("/xup", methods=['GET'])
@login_required
def xup_index():
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
    
    return render_template("xup.html", newbro=new_bro, fleet=fleet_status)


@bp_waitlist.route('/management')
@login_required
@perm_management.require(http_exception=401)
def management():
    queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first()
    return render_template("waitlist_management.html", queue=queue)

@bp_waitlist.route("/notification/<int:user_id>", methods=["GET"])
def notification(user_id):
    return render_template("notification.html", user=user_id)

@bp_waitlist.route("/debug")
@login_required
@perm_dev.require(http_exception=401)
def debug():
    return "Currently %d subscriptions" % len(subscriptions)

@bp_waitlist.route("/subscribe/<int:user_id>")
def subscribe(user_id):
    def gen(user_id):
        q = Queue()
        subscriptions.append(q)
        try:
            while True:
                result = q.get()
                if int(result.data) == user_id:
                    ev = ServerSentEvent(result.data)
                    yield ev.encode()
        finally:
            subscriptions.remove(q)

    return Response(gen(user_id), mimetype="text/event-stream")

@bp_waitlist.route("/history/")
def history_default():
    return redirect(url_for(".history", min=0, max=30))

@bp_waitlist.route("/history/<int:min>/<int:max>")
@login_required
@perm_management.require(http_exception=401)
def history(min, max):
    tnow = datetime.utcnow()
    max_time = tnow-timedelta(minutes=max)
    min_time = tnow-timedelta(minutes=min)
    history_entries = db.session.query(HistoryEntry).filter((HistoryEntry.time <= min_time) & (HistoryEntry.time > max_time)).order_by(desc(HistoryEntry.time))
    return render_template("waitlist/history.html", history=history_entries)
    