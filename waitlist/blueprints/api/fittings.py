
from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.data.perm import perm_management, perm_comphistory, perm_officer,\
    perm_leadership, perm_viewfits
from waitlist.permissions import perm_manager
from flask.globals import request
from waitlist.utility.notifications import send_notification as send_notifiaction_to_player
from waitlist import db
from waitlist.storage.database import WaitlistGroup, HistoryEntry
from waitlist.utility.json import make_json_wl, make_history_json
from flask.json import jsonify
from datetime import datetime, timedelta
import flask
from waitlist.utility import config
bp = Blueprint('api_fittings', __name__)
logger = logging.getLogger(__name__)


@bp.route("/player/<int:player_id>/notification", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def send_notification(player_id):
    waitlist_id = int(request.form['waitlistID'])
    send_notifiaction_to_player(player_id, waitlist_id, "The FC is looking for you")
    return jsonify(message="Notification send", status_code=200)


@bp.route("/waitlists/", methods=["GET"])
@login_required
def waitlist():
    group_id_str = request.args.get('group')
    try:
        group_id = int(group_id_str)
    except ValueError:
        flask.abort(400, "You are missing a Waitlist Group.")
        return None
    jsonwls = []
    group = db.session.query(WaitlistGroup).get(group_id)
    waitlists = [group.xuplist, group.logilist, group.dpslist, group.sniperlist]
    if group.otherlist is not None:
        waitlists.append(group.otherlist)
    
    # is the requester allowed to see fits?
    exclude_fits = not perm_viewfits.can()
    include_fits_from = [current_user.get_eve_id()]
    for wl in waitlists:
        jsonwls.append(make_json_wl(wl, exclude_fits, include_fits_from,
                                    scramble_names=(config.scramble_names and exclude_fits),
                                    include_names_from=include_fits_from))
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
        if perm_manager.get_permission('trainee').can():
            max_time = timedelta(minutes=30)
            if tnow - since > max_time:
                since = tnow - max_time
        else:
            max_time = timedelta(minutes=240)
            if tnow - since > max_time:
                since = tnow - max_time

    new_history_entries = db.session.query(HistoryEntry).filter(HistoryEntry.time > since).all()
    
    return jsonify(make_history_json(new_history_entries))


@bp.route("/fittings/unchecked_approve", methods=["POST"])
@login_required
@perm_comphistory.require(http_exception=401)
def unchecked_approve():
    with open('unchecked_approve.log', 'a+') as f:
        f.write(current_user.username + " tried to approve a fit/entry without checking fits\n")
    return "OK"
