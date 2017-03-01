from flask_login import login_required, current_user
from flask.globals import request
from flask.blueprints import Blueprint
import logging
import flask
from waitlist.data.sse import FitAddedSSE, EntryAddedSSE, EntryRemovedSSE,\
    FitRemovedSSE, GongSSE, Subscription, add_subscription, remove_subscription,\
    InviteMissedSSE, StatusChangedSSE
from flask.wrappers import Response

from waitlist.permissions import perm_manager

bp = Blueprint('api_sse', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('fits_view')

perm_fits_view = perm_manager.get_permission('fits_view')


def event_gen(sub: Subscription):
    if not isinstance(sub, Subscription):
        raise TypeError("Not a Subscription Object")
    add_subscription(sub)
    try:
        while True:
            event = sub.get()
            logger.debug("Event "+sub.encode(event))
            yield sub.encode(event)
    finally:
        remove_subscription(sub)


@bp.route("/", methods=["GET"])
@login_required
def events():
    """
    Available eventGroups:
    'waitlistUpdates', 'gong', 'statusChanged'
    """
    event_groups_str = request.args.get('events', None)
    if event_groups_str is None:
        flask.abort(400, "No EventGroups defined")

    event_group_strs = event_groups_str.split(",")
    event_list = []
    options = {'userId': int(current_user.get_eve_id())}
    logger.info(event_group_strs)
    group_id_str = request.args.get('groupId', None)
    if group_id_str is not None:
        options['groupId'] = int(group_id_str)
    
    if 'waitlistUpdates' in event_group_strs:
        logger.info("adding waitlist update events, to subscription")
        if group_id_str is None:
            flask.abort(400, "No GroupId defined")
        event_list += [FitAddedSSE, EntryAddedSSE, EntryRemovedSSE, FitRemovedSSE, InviteMissedSSE]
        
    if 'statusChanged' in event_group_strs:
        logger.info("Adding statusChanged event to subscription")
        event_list += [StatusChangedSSE]

    if 'gong' in event_group_strs:
        event_list += [GongSSE]
    
    # is the subscriber allowed to see fits?
    options['shouldGetFits'] = perm_fits_view.can()
        
    if len(event_list) <= 0:
        flask.abort("No valid eventgroups specified")
    subs = Subscription(event_list, options)

    return Response(event_gen(subs), mimetype="text/event-stream")
