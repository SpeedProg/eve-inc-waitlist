import gevent
from flask.json import jsonify
from waitlist.utility.json import makeJsonFitting, makeJsonWLEntry
subscriptions = []

def addSubscription(subscription):
    if not isinstance(subscription, Subscription):
        raise TypeError("Not a Subscription Object")
    subscriptions.append(subscription)

def removeSubscription(subscription):
    if not isinstance(subscription, Subscription):
        raise TypeError("Not a Subscription Object")
    subscriptions.remove(subscription)

def sendServerSentEvent(sse):
    if not isinstance(sse, ServerSentEvent):
        raise TypeError("Not a ServerSentEvent Object")
    def notify():
        for sub in subscriptions:
            if sub.acceptsEvent(sse):
                sub.put(sse)

    gevent.spawn(notify)

class Subscription(object):
    # events = [] EventClasses
    # and a function that tells if the event should be send to this subscription
    # options = {} additional data
    def __init__(self, events, options):
        self.events = events
        self.options = options
    
    def getUserId(self):
        if 'userId' not in self.options:
            return None
        return self.options['userId']
    
    def getWaitlistGroupId(self):
        if 'waitlistGroupId' not in self.options:
            return None
        return self.options['waitlistGroupId']
    
    def setWaitlistGroupId(self, groupId):
        self.options['waitlistGroupId'] = groupId
    
    def setUserId(self, userId):
        self.options['userId'] = userId
    
    def acceptsEvent(self, event):
        if event.__class__ in self.events:
            if event.__class__ in self.events and event.accepts(self):
                return True
        return False

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

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k) 
                 for k, v in self.desc_map.iteritems() if k]
        
        return "%s\n\n" % "\n".join(lines)
    
    def accepts(self):
        return True

class FitAddedSSE(ServerSentEvent):
    def __init__(self, groupId, listId, shipfit):
        ServerSentEvent.__init__(self, self.__getData(listId, shipfit), "fit-added")
        self.groupId = groupId

    def __getData(self, listId, shipfit):
        return jsonify({
            'listId': listId,
            'fit': makeJsonFitting(shipfit)
            })
    
    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId

class EntryAddedSSE(ServerSentEvent):
    def __init__(self, waitlistEntry, groupId, listId):
        ServerSentEvent.__init__(self, self.__getData(waitlistEntry, listId), "entry-added")
        self.groupId = groupId
    
    def __getData(self, waitlistEntry, listId):
        return jsonify({
            'listId': listId,
            'entry': makeJsonWLEntry(waitlistEntry)
            })
    
    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId

class EntryRemovedSSE(ServerSentEvent):
    def __init__(self, groupId, listId, entryId):
        ServerSentEvent.__init__(self, self.__getData(listId, entryId), "entry-removed")
        self.groupId = groupId
    
    def __getData(self, listId, entryId):
        return jsonify({
            'listId': listId,
            'entryId': entryId
            })
    
    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId

class FitRemovedSSE(ServerSentEvent):
    def __init__(self, groupId, listId, entryId, fitId):
        ServerSentEvent.__init__(self, self.__getData(listId, entryId, fitId), "fit-removed")
        self.groupId = groupId
        
    def __getData(self, listId, entryId, fitId):
        return jsonify({
            'listId': listId,
            'entryId': listId,
            'fitId': fitId
            })

    def accepts(self, subscription):
        return subscription.getWaitlistGroupId() == self.groupId

class GongSSE(ServerSentEvent):
    def __init__(self, userId):
        ServerSentEvent.__init__(self, self.__getData(userId), "invite-send")
        self.userId = userId
    
    def __getData(self, userId):
        return jsonify({
            'userId': userId
            })

    def accepts(self, subscription):
        return subscription.getUserId() == self.userId
