from flask_login import current_user
from flask.globals import request
from flask.blueprints import Blueprint
import logging
import flask
from waitlist.data.sse import FitAddedSSE, EntryAddedSSE, EntryRemovedSSE,\
    FitRemovedSSE, GongSSE, Subscription, add_subscription,\
    remove_subscription,\
    InviteMissedSSE, StatusChangedSSE, ReloadPageSSE
from flask.wrappers import Response

from waitlist.permissions import perm_manager
from waitlist import db
from time import sleep

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


def reload_gen():
        rpSse = ReloadPageSSE()
        while True:
            yield rpSse.encode(None)
            sleep(1000)


@bp.route("/", methods=["GET"])
def events():
    """
    Available eventGroups:
    'waitlistUpdates', 'gong', 'statusChanged'
    """
    connect_try = request.args.get('connect_try', None)

    event_groups_str = request.args.get('events', None)
    if event_groups_str is None:
        flask.abort(400, "No EventGroups defined")

    event_group_strs = event_groups_str.split(",")
    event_list = []
    ip = request.headers.get('X-Real-IP', 'NoIP')

    if not current_user.is_authenticated:
        logger.info('SSE reconnection without login on try %s from %s',
                    connect_try, ip)
        return Response(reload_gen(), mimetype="text/event-stream")

    # userId can be None for accounts that have no character set currently
    options = {'userId': current_user.get_eve_id()}

    try:
        if connect_try is not None and int(connect_try) > 0:
            logger.info('SSE reconnection for %s on try %s from %s', current_user,
                        connect_try, ip)
    except ValueError:
        logger.error('SSE connection for %s with invalid connect_try %s from %s',
                     current_user,
                     connect_try, ip)

    logger.debug('User eveId=%d requesting=%s', current_user.get_eve_id(),
                 event_group_strs)
    group_id_str = request.args.get('groupId', None)
    if group_id_str is not None:
        options['groupId'] = int(group_id_str)

    if 'waitlistUpdates' in event_group_strs:
        logger.debug("adding waitlist update events, to subscription")
        if group_id_str is None:
            flask.abort(400, "No GroupId defined")
        event_list += [FitAddedSSE, EntryAddedSSE, EntryRemovedSSE,
                       FitRemovedSSE, InviteMissedSSE]

    if 'statusChanged' in event_group_strs:
        logger.debug("Adding statusChanged event to subscription")
        event_list += [StatusChangedSSE]

    if 'gong' in event_group_strs:
        event_list += [GongSSE]

    # is the subscriber allowed to see fits?
    options['shouldGetFits'] = perm_fits_view.can()

    if len(event_list) <= 0:
        flask.abort("No valid eventgroups specified")
    subs = Subscription(event_list, options)

    # make sure there is no sqlalchemy session anymore
    db.session.remove()

    return Response(event_gen(subs), mimetype="text/event-stream")
