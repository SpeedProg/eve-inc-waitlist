import flask
from flask_login import login_required, current_user

import logging

from data.sse import FitRemovedSSE, EntryRemovedSSE, send_server_sent_event
from storage.database import Shipfit, WaitlistEntry, HistoryEntry
from utility.history_utils import create_history_object
from waitlist import db
from . import bp

logger = logging.getLogger(__name__)


@bp.route("/self/fit/<int:fitid>", methods=["DELETE"])
@login_required
def self_remove_fit(fitid):
    # remove one of your fittings by id
    fit = db.session.query(Shipfit).filter(Shipfit.id == fitid).first()
    wlentry = db.session.query(WaitlistEntry).filter(WaitlistEntry.id == fit.waitlist.id).first()

    if wlentry.user == current_user.get_eve_id():
        logger.info("%s removed their fit with id %d from group %s", current_user.get_eve_name(), fitid,
                    wlentry.waitlist.group.groupName)
        event = FitRemovedSSE(wlentry.waitlist.groupID, wlentry.waitlist_id, wlentry.id, fit.id, wlentry.user)
        wlentry.fittings.remove(fit)

        # don't delete anymore we need them for history
        # db.session.delete(fit)
        if len(wlentry.fittings) <= 0:
            event = EntryRemovedSSE(wlentry.waitlist.groupID, wlentry.waitlist_id, wlentry.id)
            db.session.delete(wlentry)

        send_server_sent_event(event)
        h_entry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_SELF_RM_FIT, None, [fit])
        h_entry.exref = wlentry.waitlist.group.groupID
        db.session.add(h_entry)
        db.session.commit()
    else:
        flask.abort(403)

    return "success"

# TODO: fittings.self_remove_wl_entry -> api_fittings.self_remove_wl_entry


@bp.route("/self/entry/<int:entry_id>", methods=["DELETE"])
@login_required
def self_remove_wl_entry(entry_id):
    # remove your self from a wl by wl entry id
    entry = db.session.query(WaitlistEntry).filter(
        (WaitlistEntry.id == entry_id) & (WaitlistEntry.user == current_user.get_eve_id())).first()
    if entry is None:
        flask.abort(404, "This Waitlist Entry does not exist.")
    event = EntryRemovedSSE(entry.waitlist.groupID, entry.waitlist_id, entry.id)
    logger.info("%s removed their own entry with id %d", current_user.get_eve_name(), entry_id)
    h_entry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_SELF_RM_ETR, None, entry.fittings)
    h_entry.exref = entry.waitlist.group.groupID
    db.session.add(h_entry)
    db.session.delete(entry)
    db.session.commit()
    send_server_sent_event(event)
    return "success"


@bp.route("/self/all_lists", methods=["DELETE"])
@login_required
def self_remove_all():
    # remove your self from all wls
    # sse list
    _events = []

    logger.info("%s removed them selfs from waitlists", current_user.get_eve_name())
    # queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first()
    # remove from all lists except queue
    entries = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == current_user.get_eve_id())
    fittings = []
    for entry in entries:
        fittings.extend(entry.fittings)

    h_entry = create_history_object(current_user.get_eve_id(), HistoryEntry.EVENT_SELF_RM_WLS_ALL, None, fittings)
    db.session.add(h_entry)

    for entry in entries:
        logger.info("%s removed own entry with id=%s", current_user.get_eve_name(), entry.id)
        event = EntryRemovedSSE(entry.waitlist.groupID, entry.waitlist_id, entry.id)
        _events.append(event)
        db.session.delete(entry)

    db.session.commit()
    for event in _events:
        send_server_sent_event(event)
    return "success"