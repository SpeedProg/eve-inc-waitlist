import logging
from datetime import datetime
from flask import request, flash, redirect, url_for, render_template, abort
from flask_login import current_user, login_required

import re

from waitlist.blueprints.api.fittings.self import self_remove_fit
from waitlist.data.names import WaitlistNames
from waitlist.data.sse import EntryAddedSSE, send_server_sent_event,\
    FitAddedSSE
from waitlist.storage.database import WaitlistGroup, WaitlistEntry, Shipfit,\
    TeamspeakDatum, InvType, FitModule, MarketGroup, HistoryEntry, Waitlist,\
    ShipCheckCollection
from waitlist.storage.modules import resist_ships, logi_ships
from waitlist.utility.history_utils import create_history_object
from waitlist.utility.fitting_utils import get_fit_format, parse_dna_fitting,\
    parse_eft, get_waitlist_type_for_fit
from waitlist.base import db
from . import bp
from flask_babel import gettext, ngettext
from typing import Dict, List, Tuple
from waitlist.utility.constants import location_flags, groups
from waitlist.utility.settings import sget_active_ts_id
from waitlist.utility.config import disable_teamspeak
import operator

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

    group_id = int(request.form['groupID'])
    logger.info("%s submitted %s for group %d", current_user.get_eve_name(), fittings, group_id)
    eve_id = current_user.get_eve_id()

    group = db.session.query(WaitlistGroup).filter(WaitlistGroup.groupID == group_id).one()

    if not group.enabled:
        # xups are disabled atm
        flash(gettext("X-UP is disabled!!!"))
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
            flash(gettext("Valid entries are scruffy [dps|logi|sniper,..]"))
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
            fit.ship_type = 0  # #System >.>
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

        flash(gettext("You were added as %(ship_type)s", ship_type=ship_type),
              "success")
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
            fit_iter = re.finditer(
                "<url=fitting:(\d+):((?:\d+_{0,1};\d+:)+:)>",
                line)
            for fitMatch in fit_iter:
                ship_type = int(fitMatch.group(1))
                dna_fit = fitMatch.group(2)
                fit = Shipfit()
                fit.ship_type = ship_type
                fit.modules = dna_fit
                mod_list = parse_dna_fitting(dna_fit)
                for location_flag, mod_map in enumerate(mod_list):
                    for mod_id in mod_map:
                        mod = mod_map[mod_id]

                        # lets check the value actually exists
                        inv_type = db.session.query(InvType).get(mod[0])
                        if inv_type is None:
                            raise ValueError(
                                'No module with ID=' + str(mod[0]))

                        db_module = FitModule(moduleID=mod[0], amount=mod[1],
                                              locationFlag=location_flag)
                        fit.moduleslist.append(db_module)
                fits.append(fit)

    fit_count = len(fits)

    logger.debug("Parsed %d fits", fit_count)

    if fit_count <= 0:
        flash(ngettext("You submitted one fit to be check by a fleet comp before getting on the waitlist.",
                       "You submitted %(num)d fits to be check by a fleet comp before getting on the waitlist.",
                       fit_count),
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

    fits_ready = []

    # split his fits into types for the different waitlist_entries
    for fit in fits:
        tag, waitlist_id = get_waitlist_type_for_fit(fit, group_id)
        fit.wl_type = tag 
        fit.targetWaitlistID = waitlist_id
        fits_ready.append(fit)

    # get the waitlist entries of this user

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
        logger.debug("%s submits %s", current_user.get_eve_name(), fit.get_dna())
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

    flash(ngettext("You submitted one fit to be check by a fleet comp before getting on the waitlist.",
                   "You submitted %(num)d fits to be check by a fleet comp before getting on the waitlist.",
                   fit_count),
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
    ts_settings = None
    ts_id = sget_active_ts_id()
    if not disable_teamspeak and ts_id is not None:
        ts_settings = db.session.query(TeamspeakDatum).get(ts_id)
    return render_template("xup.html", newbro=new_bro, group=defaultgroup,
                           groups=activegroups, ts=ts_settings)


@bp.route("/<int:fit_id>", methods=['GET'])
@login_required
def update(fit_id: int):
    new_bro: bool = current_user.is_new

    # noinspection PyPep8
    defaultgroup = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True) \
        .order_by(WaitlistGroup.ordering).first()
    # noinspection PyPep8
    activegroups = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True).all()
    ts_settings = None
    ts_id = sget_active_ts_id()
    if ts_id is not None:
        ts_settings = db.session.query(TeamspeakDatum).get(ts_id)

    return render_template("xup.html", newbro=new_bro, group=defaultgroup,
                           groups=activegroups, update=True, oldFitID=fit_id,
                           ts=ts_settings)


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
