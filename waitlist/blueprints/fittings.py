from typing import List, Tuple

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


def get_waitlist_entry_for_list(wl_id: int, creating_time: datetime, existing_entries: List[WaitlistEntry]) -> Tuple[bool, WaitlistEntry]:
    """Gets the corsponding waitlist entry or creates a new one
    The first entry of the tuple indicates if the entry was newly created
    """
    for entry in existing_entries:
        if entry.waitlist_id == wl_id:
            return False, entry
    entry = WaitlistEntry()
    entry.creation = creating_time  # for sorting entries
    entry.user = entry.user  # associate a user with the entry
    entry.waitlist_id = wl_id
    existing_entries.append(logi_entry)
    db.session.add(entry)
    return True, entry

@bp_waitlist.route("/move_to_waitlist", methods=["POST"])
@login_required
@perm_fleet_manage.require(http_exception=401)
def move_to_waitlists():
    """
    Move a whole entry to the corresponding waitlists
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


    # find out what timestamp a possibly new entry should have
    # rules are: if no wl entry, take timestamp of x-up
    #    if there is a wl entry take the waitlist entry timestamp (a random one since they should all have the same)

    new_entry_timedate = entry.creation
    for entry_t in waitlist_entries:
        if entry_t.creation < new_entry_timedate:
            new_entry_timedate = entry_t.creation

    h_entry = create_history_object(entry.user, HistoryEntry.EVENT_COMP_MV_XUP_ETR, current_user.id)
    for fit in entry.fittings:
        if fit.id not in fit_ids:
            continue
        h_entry.fittings.append(fit)

    fit_list = [fit for fit in entry.fittings]

    for fit in fit_list:
        event = FitRemovedSSE(entry.waitlist.group.groupID, entry.waitlist.id, entry.id, fit.id, entry.user)
        _sseEvents.append(event)
        entry.fittings.remove(fit)
        is_new, new_entry = get_waitlist_entry_for_list(fit.targetWaitlistID, new_entry_timedate, waitlist_entries)
        new_entry.fittings.append(fit)
        # fits in a created entry will be sent out later a whole entry
        if is_new:
            _createdEntriesList.append(new_entry)
        else:
            event = FitAddedSSE(group.grouID, new_entry.waitlist_id, new_entry.id, fit, False, new_entry.user)
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

    waitlist = fit.targetWaitlist

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

    is_entry_new, wl_entry = get_waitlist_entry_for_list(fit.targetWaitlistID, creation_time, [wl_entry] if wl_entry is not None else [])

    # remove fit from old entry
    event = FitRemovedSSE(entry.waitlist.group.groupID, entry.waitlist_id, entry.id, fit.id, entry.user)
    entry.fittings.remove(fit)
    send_server_sent_event(event)

    # add the fit to the entry
    wl_entry.fittings.append(fit)
    if not is_entry_new:
        event = FitAddedSSE(wl_entry.waitlist.group.groupID, wl_entry.waitlist_id,
                            wl_entry.id, fit, False, wl_entry.user)
        send_server_sent_event(event)

    # add a history entry
    h_entry = create_history_object(entry.user, HistoryEntry.EVENT_COMP_MV_XUP_FIT, current_user.id, [fit])
    db.session.add(h_entry)

    if is_entry_new:
        waitlist.entries.append(wl_entry)

    db.session.commit()
    if len(entry.fittings) == 0:
        event = EntryRemovedSSE(entry.waitlist.group.groupID, entry.waitlist_id, entry.id)
        db.session.delete(entry)
        db.session.commit()
        send_server_sent_event(event)

    if is_entry_new:
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
