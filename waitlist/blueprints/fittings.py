from typing import List

from flask import json
from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from flask.globals import request

from waitlist.permissions import perm_manager
from waitlist.storage.database import WaitlistEntry, Shipfit, Waitlist, HistoryEntry, WaitlistGroup
from waitlist.data.names import WaitlistNames
from werkzeug.utils import redirect
from flask.helpers import url_for
from flask.templating import render_template
from datetime import datetime, timedelta
from waitlist.base import db
from waitlist.data.sse import subscriptions, EntryAddedSSE, \
    send_server_sent_event, FitAddedSSE, FitRemovedSSE, EntryRemovedSSE
import flask
from sqlalchemy.sql.expression import desc
from waitlist.utility.history_utils import create_history_object
from waitlist.blueprints.api import fittings as fit_api

from waitlist.utility.config import stattool_enabled, stattool_uri, stattool_sri

bp_waitlist = Blueprint('fittings', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('fleet_management')
perm_manager.define_permission('fits_approve')
perm_manager.define_permission('developer_tools')
perm_manager.define_permission('comphistory_view')
perm_manager.define_permission('comphistory_unlimited')


perm_fleet_manage = perm_manager.get_permission('fleet_management')

perm_dev = perm_manager.get_permission('developer_tools')

perm_comp_view = perm_manager.get_permission('comphistory_view')
perm_comp_unlimited = perm_manager.get_permission('comphistory_unlimited')


@bp_waitlist.route("/move_to_waitlist", methods=["POST"])
@login_required
@perm_fleet_manage.require(http_exception=401)
def move_to_waitlists():
    """
    Move a whole entry to a the corresponding waitlists
    """

    # variables for SSE spawning
    _sseEvents = []
    _createdEntriesList = []

    entry_id = int(request.form['entryId'])
    fit_ids = request.form['fitIds']
    fit_ids = [int(x) for x in fit_ids.split(",")]
    entry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).first()
    if entry is None or entry.waitlist is None:
        flask.abort(404, "This entry does not exist or not belong to a waitlist anymore!")
    group: WaitlistGroup = entry.waitlist.group

    if entry is None:
        return "OK"
    logger.info("%s approved %s", current_user.username, entry.user_data.get_eve_name())

    # get waitlists in this group
    waitlist_ids = []
    for wl in group.waitlists:
        waitlist_ids.append(wl.id)

    # get all entries that are in one of these waitlists and from the current user
    waitlist_entries = db.session.query(WaitlistEntry) \
        .filter((WaitlistEntry.user == entry.user) & WaitlistEntry.waitlist_id.in_(waitlist_ids)).all()

    logi_entry = None
    sniper_entry = None
    dps_entry = None
    other_entry = None
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
            elif wl.waitlist.name == WaitlistNames.other:
                other_entry = wl

    # find out what timestamp a possibly new entry should have
    # rules are: if no wl entry, take timestamp of x-up
    #    if there is a wl entry take the waitlist entry timestamp (a random one since they should all have the same)

    new_entry_timedate = entry.creation
    for entry_t in waitlist_entries:
        if entry_t.creation < new_entry_timedate:
            new_entry_timedate = entry_t.creation

    # sort fittings by ship type
    logi = []
    dps = []
    sniper = []
    other = []
    h_entry = create_history_object(entry.user, HistoryEntry.EVENT_COMP_MV_XUP_ETR, current_user.id)
    for fit in entry.fittings:
        if fit.id not in fit_ids:
            continue
        h_entry.fittings.append(fit)

    fits_to_remove = []

    for fit in entry.fittings:
        if fit.id not in fit_ids:
            logger.info("Skipping %s because not in %s", fit, fit_ids)
            continue
        logger.info("Sorting fit %s by type into %s", str(fit), fit.wl_type)

        if fit.wl_type == WaitlistNames.logi:
            logi.append(fit)
        elif fit.wl_type == WaitlistNames.dps:
            dps.append(fit)
        elif fit.wl_type == WaitlistNames.sniper:
            sniper.append(fit)
        elif fit.wl_type == WaitlistNames.other:
            other.append(fit)
        else:
            logger.error("Failed to add %s do a waitlist.", fit)

        fits_to_remove.append(fit)

    for fit in fits_to_remove:
        event = FitRemovedSSE(entry.waitlist.group.groupID, entry.waitlist.id, entry.id, fit.id, entry.user)
        _sseEvents.append(event)
        entry.fittings.remove(fit)

    # we have a logi fit but no logi wl entry, so create one
    if len(logi) and logi_entry is None:
        logi_entry = WaitlistEntry()
        logi_entry.creation = new_entry_timedate  # for sorting entries
        logi_entry.user = entry.user  # associate a user with the entry
        group.logilist.entries.append(logi_entry)
        _createdEntriesList.append(logi_entry)

    # same for dps
    if len(dps) and dps_entry is None:
        dps_entry = WaitlistEntry()
        dps_entry.creation = new_entry_timedate  # for sorting entries
        dps_entry.user = entry.user  # associate a user with the entry
        group.dpslist.entries.append(dps_entry)
        _createdEntriesList.append(dps_entry)

    # and sniper
    if len(sniper) and sniper_entry is None:
        sniper_entry = WaitlistEntry()
        sniper_entry.creation = new_entry_timedate  # for sorting entries
        sniper_entry.user = entry.user  # associate a user with the entry
        group.sniperlist.entries.append(sniper_entry)
        _createdEntriesList.append(sniper_entry)

    # and other if other exists
    if len(other) and other_entry is None and group.otherlist is not None:
        other_entry = WaitlistEntry()
        other_entry.creation = new_entry_timedate  # for sorting entries
        other_entry.user = entry.user  # associate a user with the entry
        group.otherlist.entries.append(other_entry)
        _createdEntriesList.append(other_entry)

    # iterate over sorted fits and add them to their entry
    for logifit in logi:
        logi_entry.fittings.append(logifit)

    if logi_entry not in _createdEntriesList:
        for fit in logi:
            event = FitAddedSSE(group.groupID, logi_entry.waitlist_id, logi_entry.id, fit, False, logi_entry.user)
            _sseEvents.append(event)

    for dpsfit in dps:
        dps_entry.fittings.append(dpsfit)

    if dps_entry not in _createdEntriesList:
        for fit in dps:
            event = FitAddedSSE(group.groupID, dps_entry.waitlist_id, dps_entry.id, fit, False, dps_entry.user)
            _sseEvents.append(event)

    for sniperfit in sniper:
        sniper_entry.fittings.append(sniperfit)

    if sniper_entry not in _createdEntriesList:
        for fit in sniper:
            event = FitAddedSSE(group.groupID, sniper_entry.waitlist_id, sniper_entry.id, fit, False, sniper_entry.user)
            _sseEvents.append(event)

    # if there is no other list sort other fits in dps
    if group.otherlist is not None:
        for otherfit in other:
            other_entry.fittings.append(otherfit)

        if other_entry not in _createdEntriesList:
            for fit in other:
                event = FitAddedSSE(group.groupID, other_entry.waitlist_id, other_entry.id,
                                    fit, False, other_entry.user)
                _sseEvents.append(event)
    else:
        # it fits should go to dps wl make sure it is there
        if len(other) > 0 and dps_entry is None:
            dps_entry = WaitlistEntry()
            dps_entry.creation = new_entry_timedate  # for sorting entries
            dps_entry.user = entry.user  # associate a user with the entry
            group.dpslist.entries.append(dps_entry)
            _createdEntriesList.append(dps_entry)
        for otherfit in other:
            dps_entry.fittings.append(otherfit)

        if dps_entry not in _createdEntriesList:
            for fit in other:
                event = FitAddedSSE(group.groupID, dps_entry.waitlist_id, dps_entry.id, fit, False, dps_entry.user)
                _sseEvents.append(event)

    # add history entry to db
    db.session.add(h_entry)

    db.session.commit()

    if len(entry.fittings) <= 0:
        event = EntryRemovedSSE(entry.waitlist.group.groupID, entry.waitlist.id, entry.id)
        send_server_sent_event(event)
        db.session.delete(entry)
        db.session.commit()
    else:
        for fitEvent in _sseEvents:
            if isinstance(fitEvent, FitRemovedSSE):
                send_server_sent_event(fitEvent)

    for fitAddedEvent in _sseEvents:
        if isinstance(fitAddedEvent, FitAddedSSE):
            send_server_sent_event(fitAddedEvent)

    for createdEntry in _createdEntriesList:
        event = EntryAddedSSE(createdEntry, group.groupID, createdEntry.waitlist_id, False)
        send_server_sent_event(event)

    return "OK"


@bp_waitlist.route("/move_fit_to_waitlist", methods=["POST"])
@login_required
@perm_fleet_manage.require(http_exception=401)
def api_move_fit_to_waitlist():
    fit_id = int(request.form['fit_id'])
    fit = db.session.query(Shipfit).filter(Shipfit.id == fit_id).first()
    # fit doesn't exist or is not in a waitlist, probably double trigger when moving some one
    if fit is None or fit.waitlist is None:
        flask.abort(404, "This fit does not exist or not belong to a waitlist anymore!")

    entry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == fit.waitlist.id).first()

    group: WaitlistGroup = entry.waitlist.group

    logger.info("%s approved fit %s from %s", current_user.username, fit, entry.user_data.get_eve_name())

    # get the entry for the wl we need
    waitlist = None
    if fit.wl_type == WaitlistNames.logi:
        waitlist = group.logilist
    elif fit.wl_type == WaitlistNames.dps:
        waitlist = group.dpslist
    elif fit.wl_type == WaitlistNames.sniper:
        waitlist = group.sniperlist
    elif fit.wl_type == WaitlistNames.other:
        if group.otherlist is not None:
            waitlist = group.otherlist
        else:
            waitlist = group.dpslist

    waitlist_ids: List[int] = []
    for wl in group.waitlists:
        waitlist_ids.append(wl.id)

    waitlist_entries = db.session.query(WaitlistEntry) \
        .filter((WaitlistEntry.user == entry.user) & WaitlistEntry.waitlist_id.in_(waitlist_ids)).all()

    creation_time = entry.creation

    for centry in waitlist_entries:
        if centry.creation < creation_time:
            creation_time = centry.creation

    wl_entry = db.session.query(WaitlistEntry).join(Waitlist) \
        .filter((WaitlistEntry.user == entry.user) & (Waitlist.id == waitlist.id)).first()

    # is already on target
    if fit.waitlist is not None and wl_entry is not None and fit.waitlist.id == wl_entry.id:
        flask.abort(409, 'This fit was already moved')

    new_entry = False
    # if it doesn't exist create it
    if wl_entry is None:
        wl_entry = WaitlistEntry()
        wl_entry.creation = creation_time
        wl_entry.user = entry.user
        new_entry = True

    # remove fit from old entry
    event = FitRemovedSSE(entry.waitlist.group.groupID, entry.waitlist_id, entry.id, fit.id, entry.user)
    entry.fittings.remove(fit)
    send_server_sent_event(event)

    # add the fit to the entry
    wl_entry.fittings.append(fit)
    if not new_entry:
        event = FitAddedSSE(wl_entry.waitlist.group.groupID, wl_entry.waitlist_id,
                            wl_entry.id, fit, False, wl_entry.user)
        send_server_sent_event(event)

    # add a history entry
    h_entry = create_history_object(entry.user, HistoryEntry.EVENT_COMP_MV_XUP_FIT, current_user.id, [fit])
    db.session.add(h_entry)

    if new_entry:
        waitlist.entries.append(wl_entry)

    db.session.commit()
    if len(entry.fittings) == 0:
        event = EntryRemovedSSE(entry.waitlist.group.groupID, entry.waitlist_id, entry.id)
        db.session.delete(entry)
        db.session.commit()
        send_server_sent_event(event)

    if new_entry:
        event = EntryAddedSSE(wl_entry, wl_entry.waitlist.group.groupID, wl_entry.waitlist_id, False)
        send_server_sent_event(event)

    return "OK"


@bp_waitlist.route("/debug")
@login_required
@perm_dev.require(http_exception=401)
def debug():
    output = f"Currently {len(subscriptions)} subscriptions."
    for sub in subscriptions:
        output += json.dumps(sub.options)
    output += json.dumps(fit_api.access_duration_track)
    return output


@bp_waitlist.route("/history/")
@login_required
@perm_comp_view.require(http_exception=401)
def history_default():  
    return render_template("waitlist/history.html",
        stattool_enabled=stattool_enabled, stattool_uri=stattool_uri, stattool_sri=stattool_sri)


@bp_waitlist.route("/history/<int:min_mins>/<int:max_mins>")
@login_required
@perm_comp_view.require(http_exception=401)
def history(min_mins: int, max_mins: int):
    if max_mins <= min_mins:
        return render_template("waitlist/history_cut.html", history=[],
            stattool_enabled=stattool_enabled, stattool_uri=stattool_uri, stattool_sri=stattool_sri)
    # only officer and leadership can go back more then 4h
    if max_mins > 240 and not (perm_comp_unlimited.can()):
        redirect(url_for("fittings.history", min_mins=min_mins, max_mins=240))

    tnow: datetime = datetime.utcnow()
    max_time: datetime = tnow - timedelta(minutes=max_mins)
    min_time: datetime = tnow - timedelta(minutes=min_mins)
    history_entries = db.session.query(HistoryEntry) \
        .filter((HistoryEntry.time <= min_time) & (HistoryEntry.time > max_time)) \
        .order_by(desc(HistoryEntry.time)).limit(1000).all()
    return render_template("waitlist/history_cut.html", history=history_entries,
        stattool_enabled=stattool_enabled, stattool_uri=stattool_uri, stattool_sri=stattool_sri)
