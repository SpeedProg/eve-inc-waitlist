import logging
from datetime import datetime
from flask import request, flash, redirect, url_for, render_template, abort
from flask_login import current_user, login_required

import re

from waitlist.blueprints.api.fittings.self import self_remove_fit
from waitlist.data.names import WaitlistNames
from waitlist.data.sse import EntryAddedSSE, send_server_sent_event, FitAddedSSE
from waitlist.storage.database import WaitlistGroup, WaitlistEntry, Shipfit, InvType, FitModule, MarketGroup, HistoryEntry
from waitlist.storage.modules import resist_ships, logi_ships, sniper_ships, sniper_weapons, dps_weapons, weapongroups, \
    dps_ships, t3c_ships
from waitlist.utility.database_utils import parse_eft
from waitlist.utility.history_utils import create_history_object
from waitlist.utility.utils import get_character, get_fit_format, create_mod_map
from waitlist import db
from . import bp

logger = logging.getLogger(__name__)


@bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """
     Parse the submited fitts
     Check which fits need additional Info
     Rattlesnake, Rokh, that other ugly thing Caldari BS lvl
     Basilisk, Scimitar Logi Lvl
     -> put info into comment of the fit
     """
    # used for spawning the right SSEs
    _newEntryCreated = False
    _newFits = []

    fittings = request.form['fits']
    logger.info("%s submitted %s", current_user.get_eve_name(), fittings)
    group_id = int(request.form['groupID'])
    logger.info("%s submitted for group %s", current_user.get_eve_name(), group_id)
    eve_id = current_user.get_eve_id()

    group = db.session.query(WaitlistGroup).filter(WaitlistGroup.groupID == group_id).one()

    if not group.enabled:
        # xups are disabled atm
        flash("X-UP is disabled!!!")
        return redirect(url_for("index"))

    poke_me = 'pokeMe' in request.form

    if current_user.poke_me != poke_me:
        current_user.poke_me = poke_me
        db.session.commit()
    # check if it is scruffy
    if fittings.lower().startswith("scruffy"):
        # scruffy mode scruffy
        fittings = fittings.lower()
        _, _, ship_type = fittings.rpartition(" ")
        ship_types = []
        # check for , to see if it is a multi value shiptype
        if "," in ship_type:
            for stype in ship_type.split(","):
                stype = stype.strip()
                if stype == WaitlistNames.logi or stype == WaitlistNames.dps or stype == WaitlistNames.sniper:
                    ship_types.append(stype)
        else:
            if ship_type == WaitlistNames.logi or ship_type == WaitlistNames.dps or ship_type == WaitlistNames.sniper:
                ship_types.append(ship_type)

        # check if shiptype is valid
        if len(ship_types) <= 0:
            flash("Valid entries are scruffy [dps|logi|sniper,..]")
            return redirect(url_for('index'))

        queue = group.xuplist
        wl_entry = db.session.query(WaitlistEntry).filter(
            (WaitlistEntry.waitlist_id == queue.id) & (WaitlistEntry.user == eve_id)).first()
        if wl_entry is None:
            wl_entry = WaitlistEntry()
            wl_entry.creation = datetime.utcnow()
            wl_entry.user = eve_id
            queue.entries.append(wl_entry)
            _newEntryCreated = True

        h_entry = create_history_object(current_user.get_eve_id(), "xup")

        for stype in ship_types:
            fit = Shipfit()
            fit.ship_type = 1  # #System >.>
            fit.wl_type = stype
            fit.modules = ':'
            wl_entry.fittings.append(fit)
            if not _newEntryCreated:
                _newFits.append(fit)
            h_entry.fittings.append(fit)

        db.session.add(h_entry)
        db.session.commit()

        if _newEntryCreated:
            event = EntryAddedSSE(wl_entry, group_id, queue.id, True)
            send_server_sent_event(event)
        else:
            for fit in _newFits:
                event = FitAddedSSE(group_id, queue.id, wl_entry.id, fit, True, wl_entry.user)
                send_server_sent_event(event)

        flash(f"You were added as {ship_type}", "success")
        return redirect(url_for('index') + "?groupId=" + str(group_id))
    # ### END SCRUFFY CODE

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
    current_user.is_new = newbro

    current_user.cbs_level = caldari_bs_lvl
    current_user.lc_level = logilvl

    logger.debug("Fittings to parse: %s", fittings)

    # lets normalize linebreaks
    fittings = fittings.replace("[\n\r]+", "\n")
    fittings = fittings.strip()

    # lets first find out what kind of fitting is used
    end_line_idx = fittings.find('\n') + 1
    first_line = fittings[:end_line_idx]
    format_type = get_fit_format(first_line)

    fits = []
    if format_type == "eft":
        # split fittings up in its fittings
        string_fits = []
        fit_iter = re.finditer("\[.*,.*\]", fittings)
        s_idx = 0
        first_iter = True
        for fitMatch in fit_iter:
            if not first_iter:
                e_idx = fitMatch.start() - 1
                string_fits.append(fittings[s_idx:e_idx].split('\n'))
            else:
                first_iter = False

            s_idx = fitMatch.start()

        string_fits.append(fittings[s_idx:].split('\n'))

        logger.debug("Split fittings into %d fits", len(string_fits))

        for fit in string_fits:
            try:
                dbfit = parse_eft(fit)
                if dbfit is None:
                    abort(400, "Fit was not parseable.")
                fits.append(dbfit)
            except ValueError:
                abort(400, "Invalid module amounts")

    else:
        # parse chat links
        lines = fittings.split('\n')
        for line in lines:
            fit_iter = re.finditer("<url=fitting:(\d+):((?:\d+;\d+:)+:)>", line)
            for fitMatch in fit_iter:
                ship_type = int(fitMatch.group(1))
                dna_fit = fitMatch.group(2)
                fit = Shipfit()
                fit.ship_type = ship_type
                fit.modules = dna_fit
                mod_map = create_mod_map(dna_fit)
                for modid in mod_map:
                    mod = mod_map[modid]

                    # lets check the value actually exists
                    inv_type = db.session.query(InvType).get(mod[0])
                    if inv_type is None:
                        raise ValueError('No module with ID=' + str(mod[0]))

                    db_module = FitModule(moduleID=mod[0], amount=mod[1])
                    fit.moduleslist.append(db_module)
                fits.append(fit)

    fit_count = len(fits)

    logger.debug("Parsed %d fits", fit_count)

    if fit_count <= 0:
        flash(f"You submitted {fit_count} fits to be check by a fleet comp before getting on the waitlist.",
              "danger")
        return redirect(url_for('index') + "?groupId=" + str(group_id))

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
        try:
            mod_map = create_mod_map(fit.modules)
        except ValueError:
            abort(400, "Invalid module amounts")
        # check that ship is an allowed ship

        # it is a logi put on logi wl
        if fit.ship_type in logi_ships:
            fit.wl_type = WaitlistNames.logi
            fits_ready.append(fit)
            continue

        is_allowed = False
        if fit.ship_type in sniper_ships or fit.ship_type in dps_ships or fit.ship_type in t3c_ships:
            is_allowed = True

        if not is_allowed:  # not an allowed ship, push it on other list :P
            fit.wl_type = WaitlistNames.other
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
                market_group = db.session.query(MarketGroup).filter(
                    MarketGroup.marketGroupID == weapon_db.marketGroupID).first()
                if market_group is None:
                    continue
                parent_group = db.session.query(MarketGroup).filter(
                    MarketGroup.marketGroupID == market_group.parentGroupID).first()
                if parent_group is None:
                    continue

                # we have a parent market group
                if parent_group.marketGroupName in weapongroups['dps']:
                    weapon_type = WaitlistNames.dps
                    break
                if parent_group.marketGroupName in weapongroups['sniper']:
                    weapon_type = WaitlistNames.sniper
                    break

                    # ships with no valid weapons put on other wl
        if weapon_type == "None":
            fit.wl_type = WaitlistNames.other
            fits_ready.append(fit)
            continue

        # ships with sniper weapons put on sniper wl
        if weapon_type == WaitlistNames.sniper:
            fit.wl_type = WaitlistNames.sniper
            fits_ready.append(fit)
            continue

        if weapon_type == WaitlistNames.dps:
            fit.wl_type = WaitlistNames.dps
            fits_ready.append(fit)
            continue

    """
    #this stuff is needed somewhere else now
    # get the waitlist entries of this user

    """
    queue = group.xuplist
    wl_entry = db.session.query(WaitlistEntry).filter(
        (WaitlistEntry.waitlist_id == queue.id) & (WaitlistEntry.user == eve_id)).first()
    if wl_entry is None:
        wl_entry = WaitlistEntry()
        wl_entry.creation = datetime.utcnow()
        wl_entry.user = eve_id
        queue.entries.append(wl_entry)
        _newEntryCreated = True

    logger.info("%s submitted %s fits to be checked by a fleetcomp", current_user.get_eve_name(), len(fits_ready))

    for fit in fits_ready:
        logger.info("%s submits %s", current_user.get_eve_name(), fit.get_dna())
        wl_entry.fittings.append(fit)

    h_entry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_XUP, None, fits_ready)

    db.session.add(h_entry)
    db.session.commit()

    if _newEntryCreated:
        event = EntryAddedSSE(wl_entry, group_id, queue.id, True)
        send_server_sent_event(event)
    else:
        for fit in fits_ready:
            event = FitAddedSSE(group_id, queue.id, wl_entry.id, fit, True, wl_entry.user)
            send_server_sent_event(event)

    flash(f"You submitted {fit_count} fits to be check by a fleet comp before getting on the waitlist.",
          "success")

    return redirect(url_for('index') + "?groupId=" + str(group_id))


@bp.route('/', methods=['GET'])
@login_required
def index():
    new_bro = current_user.is_new

    # noinspection PyPep8
    defaultgroup = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True) \
        .order_by(WaitlistGroup.ordering).first()
    # noinspection PyPep8
    activegroups = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True).all()
    return render_template("xup.html", newbro=new_bro, group=defaultgroup, groups=activegroups)


@bp.route("/<int:fit_id>", methods=['GET'])
@login_required
def update(fit_id: int):
    new_bro: bool = current_user.is_new

    # noinspection PyPep8
    defaultgroup = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True) \
        .order_by(WaitlistGroup.ordering).first()
    # noinspection PyPep8
    activegroups = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True).all()
    return render_template("xup.html", newbro=new_bro, group=defaultgroup,
                           groups=activegroups, update=True, oldFitID=fit_id)


@bp.route("/update", methods=['POST'])
@login_required
def update_submit():
    oldfit_id_str = request.form.get('old-fit-id')
    try:
        old_fit_id = int(oldfit_id_str)
    except ValueError:
        abort(400, "No valid id for the fit to update given!")
        return None

    response = submit()
    self_remove_fit(old_fit_id)
    return response
