from typing import Dict, Tuple

import logging
from flask_login import login_required, current_user
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
from . import bp

logger = logging.getLogger(__name__)

# Dict that maps charids to tuple of (dt_first_access, dt_last_access)
#
access_duration_track: Dict[int, Tuple[datetime, datetime]] = {}


def get_access_duration(user_id: int, limit: timedelta, access_now: datetime) -> timedelta:
    """
    :param user_id: user id used for tracking the access duration
    :param limit: if this amount of time is between request, expire access time
    :param access_now: the datetime to use to measure this access
    :return: the amount of time some one accessed this
    """
    if user_id in access_duration_track:
        first_access, last_access = access_duration_track[user_id]
        if (access_now - last_access) > limit:  # reset
            access_duration_track[user_id] = (access_now, access_now)
            return timedelta(minutes=0)
        else:
            access_duration_track[user_id] = (first_access, access_now)
            return access_now - first_access
    else:
        access_duration_track[user_id] = (access_now, access_now)
        return timedelta(minutes=0)


perm_manager.define_permission('notification_send')
perm_manager.define_permission('comphistory_view')
perm_manager.define_permission('comphistory_unlimited')
perm_manager.define_permission('trainee')
perm_manager.define_permission('fits_approve')
perm_manager.define_permission('fits_view')
perm_manager.define_permission('comphistory_view_240')


perm_notify_send = perm_manager.get_permission('notification_send')
perm_comp_view = perm_manager.get_permission('comphistory_view')
perm_comp_unlimited = perm_manager.get_permission('comphistory_unlimited')
perm_trainee = perm_manager.get_permission('trainee')
perm_approve = perm_manager.get_permission('fits_approve')
perm_fits_view = perm_manager.get_permission('fits_view')


@bp.route("/player/<int:player_id>/notification", methods=["POST"])
@login_required
@perm_notify_send.require(http_exception=401)
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
    exclude_fits = not perm_fits_view.can()
    include_fits_from = [current_user.get_eve_id()]
    for wl in waitlists:
        jsonwls.append(make_json_wl(wl, exclude_fits, include_fits_from,
                                    scramble_names=(config.scramble_names and exclude_fits),
                                    include_names_from=include_fits_from))
    return jsonify(waitlists=jsonwls, groupName=group.groupName, groupID=group.groupID, displayName=group.displayName)


@bp.route("/history/since", methods=["GET"])
@login_required
@perm_comp_view.require(http_exception=401)
def history_since():
    laststamp = int(request.args.get('last'))
    logger.info("last=%s", str(laststamp))
    since = datetime.utcfromtimestamp(laststamp / 1000.0)
    logger.info("Looking for %s", str(since))
    tnow = datetime.utcnow()

    if not perm_comp_unlimited.can():
        if perm_manager.get_permission('comphistory_view_240').can():
            max_time = timedelta(minutes=240)
            if tnow - since > max_time:
                since = tnow - max_time
        else:
            max_time = timedelta(minutes=30)
            if tnow - since > max_time:
                since = tnow - max_time

    new_history_entries = db.session.query(HistoryEntry).filter(HistoryEntry.time > since).all()

    # do access tracking here
    if get_access_duration(current_user.id, timedelta(hours=6), datetime.utcnow()) > timedelta(days=4):
        logger.error(f"User {current_user.username}"
                     f" is requesting fits since over 4days, without a break of at least 6h")

    return jsonify(make_history_json(new_history_entries))


@bp.route("/fittings/unchecked_approve", methods=["POST"])
@login_required
@perm_approve.require(http_exception=401)
def unchecked_approve():
    with open('unchecked_approve.log', 'a+') as f:
        f.write(current_user.username + " tried to approve a fit/entry without checking fits\n")
    return "OK"
