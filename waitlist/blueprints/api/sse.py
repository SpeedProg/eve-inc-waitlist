from flask_login import login_required, current_user
from waitlist.data.perm import perm_management
from flask.globals import request
from flask.blueprints import Blueprint
import logging
import flask
from waitlist.data.sse import FitAddedSSE, EntryAddedSSE, EntryRemovedSSE,\
    FitRemovedSSE, GongSSE, Subscription, addSubscription, removeSubscription
from Queue import Queue
from flask.wrappers import Response

bp = Blueprint('api_sse', __name__)
logger = logging.getLogger(__name__)

'''
Available eventGroups:
'waitlistUpdates', 'gong'
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
    if 'waitlistUpdates' in event_group_strs:
        if perm_management.can():
            events += [FitAddedSSE, EntryAddedSSE, EntryRemovedSSE, FitRemovedSSE]
            groupId_str = request.args.get('groupId', None)
            if groupId_str is None:
                flask.abort(400, "No GroupId defined")
                options['groupId'] = int(groupId_str)

    if 'gong' in event_group_strs:
        events += [GongSSE]
        options['userId'] = int(current_user.get_eve_id())
    
    if (len(events) <= 0):
        flask.abort("No valid eventgroups specified")
    subs = Subscription(events, options)
    def gen(sub):
        if not isinstance(sub, Subscription):
            raise TypeError("Not a Subscription Object")
        q = Queue()
        addSubscription(q)
        try:
            while True:
                event = q.get()
                yield event.encode()
        finally:
            removeSubscription(q)
    

    return Response(gen(subs), mimetype="text/event-stream")