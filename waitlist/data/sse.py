import gevent
from flask.json import dumps
from waitlist.utility.json import makeJsonFitting, makeJsonWLEntry
from Queue import Queue
import logging
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
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }
    
    def setData(self, data):
        self.data = data

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k) 
                 for k, v in self.desc_map.iteritems() if k]
        
        return "%s\n\n" % "\n".join(lines)
    
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
    def __init__(self, groupId, listId, entryId, shipfit, isQueue):
        ServerSentEvent.__init__(self, self.__getData(listId, entryId, shipfit, isQueue), "fit-added")
        self.groupId = groupId

    def __getData(self, listId, entryId, shipfit, isQueue):
        return dumps({
            'listId': listId,
            'entryId': entryId,
            'isQueue': isQueue,
            'fit': makeJsonFitting(shipfit)
            })
    
    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId and subscription.getShouldGetFits()
    
    def encode(self, sub):
        return self.encode()

class EntryAddedSSE(ServerSentEvent):
    def __init__(self, waitlistEntry, groupId, listId, isQueue):
        ServerSentEvent.__init__(self, "", "entry-added")
        self.__setData(waitlistEntry, groupId, listId, isQueue) 

    def __setData(self, waitlistEntry, groupId, listId, isQueue):
        self.groupId = groupId
        self.setData({
            'groupId': groupId,
            'listId': listId,
            'isQueue': isQueue,
            'entry': makeJsonWLEntry(waitlistEntry, True)
            })

        self.jsonWithFits = ServerSentEvent.encode(self)
        self.setData({
            'groupId': groupId,
            'listId': listId,
            'isQueue': isQueue,
            'entry': makeJsonWLEntry(waitlistEntry, False)
            })
        self.jsonWOFits = ServerSentEvent.encode(self)
    
    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId
    
    def encode(self, sub):
        if (sub.getShouldGetFits()):
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
        logger.info("subGroupId " + str(subscription.getWaitlistGroupId()))
        logger.info("ownGroupId "+ str(self.groupId))
        return subscription.getWaitlistGroupId() == self.groupId
    
    def encode(self, sub):
        return self.encode()

class FitRemovedSSE(ServerSentEvent):
    def __init__(self, groupId, listId, entryId, fitId):
        ServerSentEvent.__init__(self, self.__getData(listId, entryId, fitId), "fit-removed")
        self.groupId = groupId
        
    def __getData(self, listId, entryId, fitId):
        return dumps({
            'listId': listId,
            'entryId': entryId,
            'fitId': fitId
            })

    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId and subscription.getShouldGetFits()

    def encode(self, sub):
        return self.encode()

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
