import logging
from flask import request
from flask_login import login_required, current_user

from waitlist.data.sse import EntryRemovedSSE, send_server_sent_event
from waitlist.permissions import perm_manager
from waitlist.storage.database import WaitlistGroup, WaitlistEntry, HistoryEntry, Character
from waitlist.utility.history_utils import create_history_object
from waitlist.base import db
from . import bp
import flask

logger = logging.getLogger(__name__)


perm_manager.define_permission('fleet_management')


@bp.route("/entries/remove/", methods=['POST'])
@login_required
@perm_manager.require('fleet_management')
def wl_remove_entry():
    entry_id = int(request.form['entryId'])
    entry = db.session.query(WaitlistEntry).get(entry_id)
    if entry is None:
        flask.abort(404, "Waitlist Entry does not exist!")
    h_entry = create_history_object(entry.user_data.get_eve_id(), HistoryEntry.EVENT_COM_RM_ETR, current_user.id,
                                    entry.fittings)
    h_entry.exref = entry.waitlist.group.groupID
    db.session.add(h_entry)
    logger.info("%s removed %s from waitlist %s of group %s", current_user.username, entry.user_data.get_eve_name(),
                entry.waitlist.name, entry.waitlist.group.groupName)
    event = EntryRemovedSSE(entry.waitlist.group.groupID, entry.waitlist_id, entry.id)
    db.session.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).delete()
    db.session.commit()
    send_server_sent_event(event)
    return "OK"


@bp.route("/api/wl/remove/", methods=['POST'])
@login_required
@perm_manager.require('fleet_management')
def api_wls_remove_player():
    # sse events
    _events = []

    player_id = int(request.form['playerId'])
    group_id = int(request.form['groupId'])

    if player_id is None:
        logger.error("Tried to remove player with None id from waitlists.")

    group: WaitlistGroup = db.session.query(WaitlistGroup).get(group_id)

    # don't remove from queue
    waitlist_entries = db.session.query(WaitlistEntry).filter(
        (WaitlistEntry.user == player_id) & (WaitlistEntry.waitlist_id != group.queueID)
    ).all()

    fittings = []
    for entry in waitlist_entries:
        fittings.extend(entry.fittings)

    waitlist_entries = db.session.query(WaitlistEntry).filter(
        (WaitlistEntry.user == player_id) &
        (WaitlistEntry.waitlist_id != group.queueID)
        ).all()

    for entry in waitlist_entries:
        event = EntryRemovedSSE(entry.waitlist.group.groupID, entry.waitlist_id, entry.id)
        _events.append(event)

    db.session.query(WaitlistEntry).filter(
        (WaitlistEntry.user == player_id) &
        (WaitlistEntry.waitlist_id != group.queueID)
    ).delete()

    h_entry = create_history_object(player_id, HistoryEntry.EVENT_COMP_RM_PL, current_user.id, fittings)
    h_entry.exref = group.groupID
    db.session.add(h_entry)
    db.session.commit()
    character = db.session.query(Character).filter(Character.id == player_id).first()
    logger.info("%s removed %s from %s waitlist.", current_user.username, character.eve_name, group.groupName)

    for event in _events:
        send_server_sent_event(event)

    return "OK"
