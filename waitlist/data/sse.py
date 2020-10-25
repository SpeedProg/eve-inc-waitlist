from typing import Optional

import gevent
from threading import Lock
from flask.json import dumps
from queue import Queue
import logging
from waitlist.utility.json import make_json_fitting, make_json_wl_entry
from waitlist.utility.json import make_json_constellation,\
    make_json_solar_system, make_json_station, make_json_managers, make_json_fcs
from waitlist.utility import config
logger = logging.getLogger(__name__)
subscriptions = []
subscriptions_lock = Lock()


class Subscription(object):
    # events = [] EventClasses
    # and a function that tells if the event should be send to this subscription
    # options = {} additional data
    def __init__(self, events, options):
        self.events = events
        self.options = options
        self.__q = Queue()
    
    def get_user_id(self):
        if 'userId' not in self.options:
            return None
        return self.options['userId']
    
    def get_waitlist_group_id(self):
        if 'groupId' not in self.options:
            return None
        return self.options['groupId']
    
    def set_waitlist_group_id(self, group_id):
        self.options['groupId'] = group_id
    
    def set_user_id(self, user_id):
        self.options['userId'] = user_id
    
    def set_should_get_fits(self, should_get_fits):
        self.options['shouldGetFits'] = should_get_fits
    
    def get_should_get_fits(self):
        return self.options['shouldGetFits']
    
    def accepts_event(self, event):
        logger.debug("Should we accept "+event.__class__.__name__)
        if event.__class__ in self.events:
            logger.debug("Event is in configured events")
            if event.accepts(self):
                logger.debug("Event should go to this subscription")
                return True
            else:
                logger.debug("Event should not go to this subscription")
        else:
            logger.debug("Event is not configured in this subscription")
        return False
    
    def get(self):
        return self.__q.get()
    
    def put(self, element):
        return self.__q.put(element)
    
    def encode(self, event):
        return event.encode(self)


def add_subscription(subscription: Subscription):
    if not isinstance(subscription, Subscription):
        raise TypeError("Not a Subscription Object")
    with subscriptions_lock:
        subscriptions.append(subscription)
    logger.info('Adding subscription for %s', subscription.get_user_id())


def remove_subscription(subscription):
    if not isinstance(subscription, Subscription):
        raise TypeError("Not a Subscription Object")
    with subscriptions_lock:
        subscriptions.remove(subscription)
    logger.info('Removing subscription for %s', subscription.get_user_id())


# this class should never be used only extended classes
class ServerSentEvent(object):
    def __init__(self, data: str, event: Optional[str]=None, _id: Optional[int]=None):
        self.data = data
        self.event = event
        self.id = _id
        
        self.desc_map = {
            "data": "data",
            "event": "event",
            "id": "id"
        }
    
    def set_data(self, data):
        self.data = data

    def encode(self, sub):
        if not self.data:
            logger.error("No Data Set")
            raise RuntimeError("Data not set for SSE event")

        lines = ["%s: %s" % (k, self.get_value(v))
                 for k, v in list(self.desc_map.items()) if hasattr(self, v) and self.get_value(v)]
        
        return "%s\n\n" % "\n".join(lines)
    
    def get_value(self, name):
        return getattr(self, name)
    
    def accepts(self, subscription):
        return True


def send_server_sent_event(sse):
    if not isinstance(sse, ServerSentEvent):
        raise TypeError("Not a ServerSentEvent Object")
    
    def notify():
        with subscriptions_lock:
            for sub in subscriptions:
                if sub.accepts_event(sse):
                    sub.put(sse)

    gevent.spawn(notify)


class FitAddedSSE(ServerSentEvent):
    def __init__(self, group_id, list_id, entry_id, ship_fit, is_queue, user_id):
        ServerSentEvent.__init__(self, self.__get_data(list_id, entry_id, ship_fit, is_queue, user_id), "fit-added")
        self.groupId = group_id
        self.userId = user_id

    @classmethod
    def __get_data(cls, list_id, entry_id, ship_fit, is_queue, user_id):
        return dumps({
            'listId': list_id,
            'entryId': entry_id,
            'isQueue': is_queue,
            'userId': user_id,
            'fit': make_json_fitting(ship_fit)
            })
    
    def accepts(self, subscription):
        logger.debug("FitAddedSSE")
        logger.debug("Should GetFit: " + str(subscription.get_should_get_fits()))
        logger.debug("UserIds " + str(subscription.get_user_id()) + "=" + str(self.userId))
        logger.debug("IDs Same " + str(subscription.get_user_id() == self.userId))
        return subscription.get_waitlist_group_id() == self.groupId and (
            subscription.get_should_get_fits() or subscription.get_user_id() == self.userId
            )
    
    def encode(self, sub):
        return ServerSentEvent.encode(self, sub)


class EntryAddedSSE(ServerSentEvent):
    def __init__(self, waitlist_entry, group_id, list_id, is_queue):
        ServerSentEvent.__init__(self, "", "entry-added")
        self.__set_data(waitlist_entry, group_id, list_id, is_queue, waitlist_entry.user)

    def __set_data(self, waitlist_entry, group_id, list_id, is_queue, user_id):
        self.groupId = group_id
        self.userId = user_id
        self.set_data(dumps({
            'groupId': group_id,
            'listId': list_id,
            'isQueue': is_queue,
            'entry': make_json_wl_entry(waitlist_entry, False)
            }))

        self.jsonWithFits = ServerSentEvent.encode(self, None)
        self.set_data(dumps({
            'groupId': group_id,
            'listId': list_id,
            'isQueue': is_queue,
            'entry': make_json_wl_entry(waitlist_entry, True, scramble_names=config.scramble_names)
            }))
        self.jsonWOFits = ServerSentEvent.encode(self, None)
    
    def accepts(self, subscription):
        logger.debug("EntryAddedSSE")
        logger.debug("Should GetFit: " + str(subscription.get_should_get_fits()))
        logger.debug("UserIds " + str(subscription.get_user_id()) + "=" + str(self.userId))
        logger.debug("IDs Same " + str(subscription.get_user_id() == self.userId))
        return subscription.get_waitlist_group_id() == self.groupId
    
    def encode(self, sub):
        if sub.get_should_get_fits() or sub.get_user_id() == self.userId:
            return self.jsonWithFits
        return self.jsonWOFits


class EntryRemovedSSE(ServerSentEvent):
    def __init__(self, group_id, list_id, entry_id):
        ServerSentEvent.__init__(self, self.__get_data(list_id, entry_id), "entry-removed")
        self.groupId = group_id

    @classmethod
    def __get_data(cls, list_id, entry_id):
        return dumps({
            'listId': list_id,
            'entryId': entry_id
            })
    
    def accepts(self, subscription):
        logger.debug("subGroupId " + str(subscription.get_waitlist_group_id()))
        logger.debug("ownGroupId " + str(self.groupId))
        return subscription.get_waitlist_group_id() == self.groupId
    
    def encode(self, sub):
        return ServerSentEvent.encode(self, sub)


class FitRemovedSSE(ServerSentEvent):
    def __init__(self, group_id, list_id, entry_id, fit_id, user_id):
        ServerSentEvent.__init__(self, self.__get_data(list_id, entry_id, fit_id), "fit-removed")
        self.groupId = group_id
        self.userId = user_id

    @classmethod
    def __get_data(cls, list_id, entry_id, fit_id):
        return dumps({
            'listId': list_id,
            'entryId': entry_id,
            'fitId': fit_id
            })

    def accepts(self, subscription):
        return subscription.get_waitlist_group_id() == self.groupId and (
            subscription.get_should_get_fits() or subscription.get_user_id() == self.userId
            )

    def encode(self, sub):
        return ServerSentEvent.encode(self, sub)


class GongSSE(ServerSentEvent):
    def __init__(self, user_id):
        ServerSentEvent.__init__(self, self.__get_data(user_id), "invite-send")
        self.userId = user_id

    @classmethod
    def __get_data(cls, user_id):
        return dumps({
            'userId': user_id
            })

    def accepts(self, subscription):
        return subscription.get_user_id() == self.userId
    
    def encode(self, sub):
        return ServerSentEvent.encode(self, sub)


class InviteMissedSSE(ServerSentEvent):
    def __init__(self, group_id, user_id):
        ServerSentEvent.__init__(self, self.__get_data(user_id), "invite-missed")
        self.groupId = group_id

    @classmethod
    def __get_data(cls, user_id):
        return dumps({
            'userId': user_id
            })

    def accepts(self, subscription):
        return True
    
    def encode(self, sub):
        return ServerSentEvent.encode(self, sub)


class StatusChangedSSE(ServerSentEvent):
    def __init__(self, group):
        ServerSentEvent.__init__(self, self.__get_data(group), "status-changed")
        self.groupId = group.groupID

    @classmethod
    def __get_data(cls, group):
        return dumps({
            'groupID': group.groupID,
            'status': group.status,
            'enabled': group.enabled,
            'influence': group.influence,
            'constellation': make_json_constellation(group.constellation),
            'solarSystem': make_json_solar_system(group.system),
            'station': make_json_station(group.dockup),
            'fcs': make_json_fcs(group.fcs),
            'managers': make_json_managers(group),
            })

    def accepts(self, subscription):
        sub_group_id = subscription.get_waitlist_group_id()
        return sub_group_id is None or sub_group_id == self.groupId

    def encode(self, sub: Subscription):
        return ServerSentEvent.encode(self, sub)


class ReloadPageSSE(ServerSentEvent):
    def __init__(self):
        super(ReloadPageSSE, self).__init__(True, 'reload')

    def accepts(self, sub: Subscription):
        return True

    def encode(self, sub: Subscription):
        return super(ReloadPageSSE, self).encode(sub)
