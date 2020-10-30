import logging
from waitlist.storage.database import Waitlist, Character, HistoryEntry
from waitlist.base import db
import flask
from waitlist.data.sse import GongSSE, send_server_sent_event
from waitlist.utility.history_utils import create_history_object
from flask_login import current_user
from waitlist.utility.coms import get_connector
from waitlist.utility import config
logger = logging.getLogger(__name__)


def send_notification(player_id: int, waitlist_id: int, message: str = "You are invited to fleet as {0}") -> None:
    if player_id is None:
        logger.error("Tried to send notification to player with None ID.")
        flask.abort(400, "Tried to send notification to player with None ID")

    # lets check that the given wl exists
    waitlist = db.session.query(Waitlist).get(waitlist_id)
    if waitlist is None:
        logger.error("Given waitlist id %s is not valid.", str(waitlist_id))
        flask.abort(400, f"Given waitlist id {waitlist_id} is not valid.")
    # don't remove from queue
    # queue = db.session.query(Waitlist).filter(Waitlist.name == WaitlistNames.xup_queue).first()

    # db.session.query(WaitlistEntry).filter((WaitlistEntry.user == playerId)
    #  & (WaitlistEntry.waitlist_id != queue.id)).delete()
    # db.session.commit()
    event = GongSSE(player_id)
    send_server_sent_event(event)

    # publish(event)

    character = db.session.query(Character).filter(Character.id == player_id).first()
    com_connector = get_connector()
    if com_connector is not None and character.poke_me:  # only poke if he didn't disable it
        msg = None
        try:
            msg = message.format(waitlist.name)
        except:
            msg = message
        com_connector.send_notification(character.eve_name, msg)

    h_entry = create_history_object(character.get_eve_id(), HistoryEntry.EVENT_COMP_NOTI_PL, current_user.id)
    h_entry.exref = waitlist.group.groupID

    db.session.add(h_entry)

    db.session.commit()
    logger.info("%s send notification to %s.", current_user.username, character.eve_name)

