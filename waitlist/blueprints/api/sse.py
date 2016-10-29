from __future__ import absolute_import
from flask_login import login_required, current_user
from waitlist.data.perm import perm_viewfits
from flask.globals import request
from flask.blueprints import Blueprint
import logging
import flask
from waitlist.data.sse import FitAddedSSE, EntryAddedSSE, EntryRemovedSSE,\
    FitRemovedSSE, GongSSE, Subscription, addSubscription, removeSubscription,\
    InviteMissedSSE, StatusChangedSSE
from flask.wrappers import Response

bp = Blueprint('api_sse', __name__)
logger = logging.getLogger(__name__)

def eventGen(sub):
    if not isinstance(sub, Subscription):
        raise TypeError("Not a Subscription Object")
    addSubscription(sub)
    try:
        while True:
            event = sub.get()
            logger.debug("Event "+sub.encode(event))
            yield sub.encode(event)
    finally:
        removeSubscription(sub)

'''
Available eventGroups:
'waitlistUpdates', 'gong', 'statusChanged'
'''
@bp.route("/", methods=["GET"])
@login_required
def events():
    event_groups_str = request.args.get('events', None)
    if event_groups_str is None:
        flask.abort(400, "No EventGroups defined")

    event_group_strs = event_groups_str.split(",")
    events = []
    options = {}
    options['userId'] = int(current_user.get_eve_id())
    logger.info(event_group_strs);
    
    if 'waitlistUpdates' in event_group_strs or 'statusChanged' in event_group_strs:
        groupId_str = request.args.get('groupId', None)
        if groupId_str is None:
            flask.abort(400, "No GroupId defined")
        options['groupId'] = int(groupId_str)
    
    if 'waitlistUpdates' in event_group_strs:
        logger.info("adding waitlist update events, to subscription")
        events += [FitAddedSSE, EntryAddedSSE, EntryRemovedSSE, FitRemovedSSE, InviteMissedSSE]

    if 'statusChanged' in event_group_strs:
        logger.info("Adding statusChanged event to subscription")
        events += [StatusChangedSSE]

    if 'gong' in event_group_strs:
        events += [GongSSE]
    
    # is the subscriber allowed to see fits?
    options['shouldGetFits'] = perm_viewfits.can()
        
    
    if (len(events) <= 0):
        flask.abort("No valid eventgroups specified")
    subs = Subscription(events, options)

    return Response(eventGen(subs), mimetype="text/event-stream")