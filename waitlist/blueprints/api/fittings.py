from __future__ import absolute_import
from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.data.perm import perm_management, perm_comphistory, perm_officer,\
    perm_leadership, perm_viewfits
from waitlist.permissions import perm_manager
from flask.globals import request
from waitlist.utility.notifications import send_notification as send_notifiaction_to_player
from waitlist.base import db
from waitlist.storage.database import WaitlistGroup, HistoryEntry
from waitlist.utility.json import makeJsonWL, makeHistoryJson
from flask.json import jsonify
from datetime import datetime, timedelta
import flask
from waitlist.utility import config
bp = Blueprint('api_fittings', __name__)
logger = logging.getLogger(__name__)

@bp.route("/player/<int:playerID>/notification", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def send_notification(playerID):
    waitlistID = int(request.form['waitlistID'])
    send_notifiaction_to_player(playerID, waitlistID, "The FC is looking for you")
    return jsonify(message="Notification send", status_code=200)

@bp.route("/waitlists/", methods=["GET"])
@login_required
def waitlist():
    groupId_str = request.args.get('group')
    try:
        group_id = int(groupId_str)
    except ValueError:
        flask.abort(400, "You are missing a Waitlist Group.")
    jsonwls = []
    group = db.session.query(WaitlistGroup).get(group_id)
    waitlists = [group.xuplist, group.logilist, group.dpslist, group.sniperlist]
    if group.otherlist is not None:
        waitlists.append(group.otherlist)
    
    # is the requester allowed to see fits?
    excludeFits = not perm_viewfits.can()
    includeFitsFrom = [current_user.get_eve_id()]
    for wl in waitlists:
        jsonwls.append(makeJsonWL(wl, excludeFits, includeFitsFrom, scramble_names=(config.scramble_names and excludeFits), include_names_from=includeFitsFrom))
    return jsonify(waitlists=jsonwls, groupName=group.groupName, groupID=group.groupID, displayName=group.displayName)

@bp.route("/history/since", methods=["GET"])
@login_required
@perm_comphistory.require(http_exception=401)
def history_since():
    laststamp = int(request.args.get('last'))
    logger.info("last=%s", str(laststamp))
    since = datetime.utcfromtimestamp(laststamp / 1000.0)
    logger.info("Looking for %s", str(since))
    tnow = datetime.utcnow()

    if not (perm_officer.can() or perm_leadership.can()):
        if (perm_manager.getPermission('trainee').can()):
            maxTime = timedelta(minutes=30)
            if tnow - since > maxTime:
                since = tnow - maxTime
        else:
            maxTime = timedelta(minutes=240)
            if tnow - since > maxTime:
                since = tnow - maxTime

    newHistoryEntries = db.session.query(HistoryEntry).filter(HistoryEntry.time > since).all()
    
    return jsonify(makeHistoryJson(newHistoryEntries))

@bp.route("/fittings/unchecked_approve", methods=["POST"])
@login_required
@perm_comphistory.require(http_exception=401)
def unchecked_approve():
    with open('unchecked_approve.log', 'a+') as f:
        f.write(current_user.username + " tried to approve a fit/entry without checking fits\n")
    return "OK"
