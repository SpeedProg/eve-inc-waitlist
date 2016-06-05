from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
import flask
from flask.globals import request
from waitlist.data.perm import perm_management
from waitlist.storage.database import CrestFleet, Waitlist, WaitlistGroup,\
    Character, WaitlistEntry, HistoryEntry, HistoryExtInvite
from waitlist.utility.notifications import send_notification
from waitlist.utility.history_utils import create_history_object
from waitlist.utility.fleet import spawn_invite_check, invite, member_info
from flask.json import jsonify
from waitlist.base import db
from datetime import datetime
from flask.wrappers import Response
bp = Blueprint('api_fleet', __name__)
logger = logging.getLogger(__name__)

@bp.route("/<int:fleetID>/", methods=["DELETE"])
@login_required
@perm_management.require(http_exception=401)
def removeFleet(fleetID):
    logger.info("%s deletes crest fleet %i", current_user.username, fleetID)
    db.session.query(CrestFleet).filter(CrestFleet.fleetID == fleetID).delete()
    db.session.commit()
    return flask.jsonify(status_code=200, message="Fleet Deleted")

@bp.route("/fleet/members/", methods=['POST'])
@login_required
@perm_management.require(http_exception=401)
def invite_to_fleet():
    characterID = int(request.form.get('charID'))
    waitlistID = int(request.form.get('waitlistID'))
    groupID = int(request.form.get('groupID'))
    
    send_notification(characterID, waitlistID)

    waitlist = db.session.query(Waitlist).filter(Waitlist.id == waitlistID).first();
    squad_type = waitlist.name
        # lets check that the given wl exists
    if waitlist is None:
        logger.error("Given waitlist ID=%d is not valid.", waitlistID)
        flask.abort(400)

    character = db.session.query(Character).get(characterID)
    logger.info("Invited %s by %s into %s", character.eve_name, current_user.username, squad_type)
    if current_user.fleet is None:
        logger.info("%s is currently not not boss of a fleet, he can't invite people.", current_user.username)
        resp = jsonify(status_code=409, message="You are not currently Boss of a Fleet")
        resp.status_code = 409
        return resp
    fleet = current_user.fleet
    
    # generate a list in which order squads should be preferred in case the main squad is full
    squadIDList = []
    if squad_type == "logi":
        squadIDList = [(fleet.logiWingID, fleet.logiSquadID), (fleet.otherWingID, fleet.otherSquadID), (fleet.sniperWingID, fleet.sniperSquadID), (fleet.dpsWingID, fleet.dpsSquadID)]
    elif squad_type == "dps":
        squadIDList = [(fleet.dpsWingID, fleet.dpsSquadID), (fleet.otherWingID, fleet.otherSquadID), (fleet.sniperWingID, fleet.sniperSquadID), (fleet.logiWingID, fleet.logiSquadID)]
    elif squad_type == "sniper":
        squadIDList = [(fleet.sniperWingID, fleet.sniperSquadID), (fleet.otherWingID, fleet.otherSquadID), (fleet.dpsWingID, fleet.dpsSquadID), (fleet.logiWingID, fleet.logiSquadID)]
    else:
        return Response(flask.jsonify({'message': 'Unknown Squad Type'}), 415)

    # invite over crest and get back the status
    status = invite(characterID, squadIDList)
    
    resp = flask.jsonify({'status': status['status_code'], 'message': status['text']})
    resp.status_code = status['status_code']

    
    character = db.session.query(Character).filter(Character.id == characterID).first()
    hEntry = create_history_object(character.get_eve_id(), HistoryEntry.EVENT_COMP_INV_PL, current_user.id)
    hEntry.exref = waitlist.group.groupID
    
    # create a invite history extension
    # get wl entry for creation time
    wlEntry = db.session.query(WaitlistEntry).filter((WaitlistEntry.waitlist_id == waitlistID) & (WaitlistEntry.user == characterID)).first()
    if wlEntry == None:
        logger.error("Waitlist Entry with ID=%d does not exist!", waitlistID)
        return resp
    
    db.session.add(hEntry)
    db.session.flush()
    db.session.refresh(hEntry)
    
    historyExt = HistoryExtInvite()
    historyExt.historyID = hEntry.historyID
    historyExt.waitlistID = waitlistID
    historyExt.timeCreated = wlEntry.creation
    historyExt.timeInvited = datetime.utcnow()
    db.session.add(historyExt)

    db.session.commit()
    logger.info("%s invited %s to fleet from %s.", current_user.username, character.eve_name, waitlist.group.groupName)
    
    # set a timer for 1min and 6s that checks if the person accepted the invite
    logger.info("API Response for %s was %d", character.eve_name, resp.status_code)
    if resp.status_code == 201:
        spawn_invite_check(characterID, groupID, fleet.fleetID)
    return resp
