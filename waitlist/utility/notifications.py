import logging
from waitlist.storage.database import Waitlist, Character, HistoryEntry
from waitlist import db
import flask
from waitlist.data.sse import InviteEvent
from waitlist.utility.history_utils import create_history_object
from flask_login import current_user
from waitlist.ts3.connection import send_poke
from ts3.query import TS3QueryError
logger = logging.getLogger(__name__)

import gevent
subscriptions = []

def send_invite_notice(data):
    def notify():
        for sub in subscriptions:
            sub.put(data)

    gevent.spawn(notify)

def send_notification(playerID, waitlistID):
    if playerID == None:
        logger.error("Tried to remove player with None id from waitlists.")
    
    # lets check that the given wl exists
    waitlist = db.session.query(Waitlist).get(waitlistID);
    if waitlist is None:
        logger.error("Given waitlist id %s is not valid.", str(waitlistID))
        flask.abort(400)
    # don't remove from queue
    #queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first()
    
    #db.session.query(WaitlistEntry).filter((WaitlistEntry.user == playerId) & (WaitlistEntry.waitlist_id != queue.id)).delete()
    #db.session.commit()
    event = InviteEvent(playerID)
    send_invite_notice(event)

    #publish(event)
    
    character = db.session.query(Character).filter(Character.id == playerID).first()
    try: 
        send_poke(character.eve_name, "You are invited to fleet as %s" % waitlist.name)
    except TS3QueryError:
        pass # ignore it a user that is not on TS
        
    hEntry = create_history_object(character.get_eve_id(), HistoryEntry.EVENT_COMP_NOTI_PL, current_user.id)
    hEntry.exref = waitlist.group.groupID
    
  
    db.session.add(hEntry)

    db.session.commit()
    logger.info("%s send notification to %s.", current_user.username, character.eve_name)