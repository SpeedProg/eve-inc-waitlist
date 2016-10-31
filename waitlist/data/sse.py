from __future__ import absolute_import
import gevent
from flask.json import dumps
from Queue import Queue
import logging
from waitlist.utility.json import makeJsonFitting, makeJsonWLEntry
from waitlist.utility.json import makeJsonConstellation,\
    makeJsonSolarSystem, makeJsonStation, makeJsonManagers, makeJsonFCs
from waitlist.utility import config
logger = logging.getLogger(__name__)
subscriptions = []

class Subscription(object):
    # events = [] EventClasses
    # and a function that tells if the event should be send to this subscription
    # options = {} additional data
    def __init__(self, events, options):
        self.events = events
        self.options = options
        self.__q = Queue()
    
    def getUserId(self):
        if 'userId' not in self.options:
            return None
        return self.options['userId']
    
    def getWaitlistGroupId(self):
        if 'groupId' not in self.options:
            return None
        return self.options['groupId']
    
    def setWaitlistGroupId(self, groupId):
        self.options['groupId'] = groupId
    
    def setUserId(self, userId):
        self.options['userId'] = userId
    
    def setShouldGetFits(self, shouldGetFits):
        self.options['shouldGetFits'] = shouldGetFits
    
    def getShouldGetFits(self):
        return self.options['shouldGetFits']
    
    def acceptsEvent(self, event):
        logger.info("Should we accept "+event.__class__.__name__)
        if event.__class__ in self.events:
            logger.info("Event is in configured events")
            if event.accepts(self):
                logger.info("Event should go to this subscription")
                return True
            else:
                logger.info("Event should not go to this subscription")
        else:
            logger.info("Event is not configured in this subscription")
        return False
    
    def get(self):
        return self.__q.get()
    
    def put(self, element):
        return self.__q.put(element)
    
    def encode(self, event):
        return event.encode(self)

def addSubscription(subscription):
    if not isinstance(subscription, Subscription):
        raise TypeError("Not a Subscription Object")
    subscriptions.append(subscription)

def removeSubscription(subscription):
    if not isinstance(subscription, Subscription):
        raise TypeError("Not a Subscription Object")
    subscriptions.remove(subscription)

# this class should never be used only extended classes
class ServerSentEvent(object):
    def __init__(self, data, event = None, _id = None):
        self.data = data
        self.event = event
        self.id = _id
        
        self.desc_map = {
            "data" : "data",
            "event" : "event",
            "id" : "id"
        }
    
    def setData(self, data):
        self.data = data

    def encode(self):
        if not self.data:
            logger.info("No Data Set")
            return ""

        lines = ["%s: %s" % (k, self.getValue(v)) 
                 for k, v in self.desc_map.iteritems() if hasattr(self, v) and self.getValue(v)]
        
        return "%s\n\n" % "\n".join(lines)
    
    def getValue(self, name):
        return getattr(self, name)
    
    def accepts(self, subscription):
        return True

def sendServerSentEvent(sse):
    if not isinstance(sse, ServerSentEvent):
        raise TypeError("Not a ServerSentEvent Object")
    
    def notify():
        for sub in subscriptions:
            if sub.acceptsEvent(sse):
                sub.put(sse)

    gevent.spawn(notify)

class FitAddedSSE(ServerSentEvent):
    def __init__(self, groupId, listId, entryId, shipfit, isQueue, userId):
        ServerSentEvent.__init__(self, self.__getData(listId, entryId, shipfit, isQueue, userId), "fit-added")
        self.groupId = groupId
        self.userId = userId

    def __getData(self, listId, entryId, shipfit, isQueue, userId):
        return dumps({
            'listId': listId,
            'entryId': entryId,
            'isQueue': isQueue,
            'userId': userId,
            'fit': makeJsonFitting(shipfit)
            })
    
    def accepts(self, subscription):
        logger.debug("FitAddedSSE")
        logger.debug("Should GetFit: "+str(subscription.getShouldGetFits()))
        logger.debug("UserIds "+str(subscription.getUserId())+"="+str(self.userId))
        logger.debug("IDs Same "+str(subscription.getUserId() == self.userId))
        return subscription.getWaitlistGroupId() == self.groupId and (
            subscription.getShouldGetFits() or subscription.getUserId() == self.userId
            )
    
    def encode(self, sub):
        return ServerSentEvent.encode(self)

class EntryAddedSSE(ServerSentEvent):
    def __init__(self, waitlistEntry, groupId, listId, isQueue):
        ServerSentEvent.__init__(self, "", "entry-added")
        self.__setData(waitlistEntry, groupId, listId, isQueue, waitlistEntry.user)

    def __setData(self, waitlistEntry, groupId, listId, isQueue, userId):
        self.groupId = groupId
        self.userId = userId
        self.setData(dumps({
            'groupId': groupId,
            'listId': listId,
            'isQueue': isQueue,
            'entry': makeJsonWLEntry(waitlistEntry, False)
            }))

        self.jsonWithFits = ServerSentEvent.encode(self)
        self.setData(dumps({
            'groupId': groupId,
            'listId': listId,
            'isQueue': isQueue,
            'entry': makeJsonWLEntry(waitlistEntry, True, scramble_names=config.scramble_names_on_public_api)
            }))
        self.jsonWOFits = ServerSentEvent.encode(self)
    
    def accepts(self, subscription):
        logger.info("EntryAddedSSE")
        logger.info("Should GetFit: "+str(subscription.getShouldGetFits()))
        logger.info("UserIds "+str(subscription.getUserId())+"="+str(self.userId))
        logger.info("IDs Same "+str(subscription.getUserId() == self.userId))
        return subscription.getWaitlistGroupId() == self.groupId
    
    def encode(self, sub):
        if (sub.getShouldGetFits() or sub.getUserId() == self.userId):
            return self.jsonWithFits
        return self.jsonWOFits


class EntryRemovedSSE(ServerSentEvent):
    def __init__(self, groupId, listId, entryId):
        ServerSentEvent.__init__(self, self.__getData(listId, entryId), "entry-removed")
        self.groupId = groupId
    
    def __getData(self, listId, entryId):
        return dumps({
            'listId': listId,
            'entryId': entryId
            })
    
    def accepts(self, subscription):
        logger.debug("subGroupId " + str(subscription.getWaitlistGroupId()))
        logger.debug("ownGroupId "+ str(self.groupId))
        return subscription.getWaitlistGroupId() == self.groupId
    
    def encode(self, sub):
        return ServerSentEvent.encode(self)

class FitRemovedSSE(ServerSentEvent):
    def __init__(self, groupId, listId, entryId, fitId, userId):
        ServerSentEvent.__init__(self, self.__getData(listId, entryId, fitId), "fit-removed")
        self.groupId = groupId
        self.userId = userId
        
    def __getData(self, listId, entryId, fitId):
        return dumps({
            'listId': listId,
            'entryId': entryId,
            'fitId': fitId
            })

    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId and (
            subscription.getShouldGetFits() or subscription.getUserId() == self.userId
            )

    def encode(self, sub):
        return ServerSentEvent.encode(self)

class GongSSE(ServerSentEvent):
    def __init__(self, userId):
        ServerSentEvent.__init__(self, self.__getData(userId), "invite-send")
        self.userId = userId
    
    def __getData(self, userId):
        return dumps({
            'userId': userId
            })

    def accepts(self, subscription):
        return subscription.getUserId() == self.userId
    
    def encode(self, sub):
        return ServerSentEvent.encode(self)

class InviteMissedSSE(ServerSentEvent):
    def __init__(self, groupId, userId):
        ServerSentEvent.__init__(self, self.__getData(userId), "invite-missed")
        self.groupId = groupId
    
    def __getData(self, userId):
        return dumps({
            'userId': userId
            })

    def accepts(self, subscription):
        return True
    
    def encode(self, sub):
        return ServerSentEvent.encode(self)

class StatusChangedSSE(ServerSentEvent):
    def __init__(self, group):
        ServerSentEvent.__init__(self, self.__getData(group), "status-changed")
        self.groupId = group.groupID

    def __getData(self, group):
        return dumps({
            'groupID': group.groupID,
            'status': group.status,
            'enabled': group.enabled,
            'influence': group.influence,
            'constellation': makeJsonConstellation(group.constellation),
            'solarSystem': makeJsonSolarSystem(group.system),
            'station': makeJsonStation(group.dockup),
            'fcs': makeJsonFCs(group.fcs),
            'managers': makeJsonManagers(group),
            })

    def accepts(self, subscription):
        subGroupId = subscription.getWaitlistGroupId()
        return subGroupId is None or subGroupId == self.groupId

    def encode(self, sub):
        return ServerSentEvent.encode(self)