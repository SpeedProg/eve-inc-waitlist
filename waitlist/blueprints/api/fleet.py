from __future__ import absolute_import
from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
import flask
from flask.globals import request
from waitlist.data.perm import perm_management
from waitlist.storage.database import CrestFleet, Waitlist,\
    Character, WaitlistEntry, HistoryEntry, HistoryExtInvite, Setting,\
    TeamspeakDatum
from waitlist.utility.notifications import send_notification
from waitlist.utility.history_utils import create_history_object
from waitlist.utility.fleet import spawn_invite_check, invite, member_info
from flask.json import jsonify
from waitlist.base import db
from datetime import datetime
from flask.wrappers import Response
from waitlist.utility.eve_id_utils import get_character_by_name
from flask.helpers import make_response
from waitlist.ts3.connection import move_to_safety_channel
from waitlist.utility.settings.settings import sget_active_ts_id
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

@bp.route("/fleet/actions/invite/<string:name>", methods=['POST'])
@login_required
@perm_management.require()
def fleet_actions_invite(name):
    character = get_character_by_name(name)
    fleet = current_user.fleet
    logger.info("%s invites %s by name to fleet %d", current_user.username, name, fleet.fleetID)
    status = invite(character.id, [(fleet.dpsWingID, fleet.dpsSquadID), (fleet.otherWingID, fleet.otherSquadID), (fleet.sniperWingID, fleet.sniperSquadID), (fleet.logiWingID, fleet.logiSquadID)])
    hEntry = create_history_object(character.get_eve_id(), HistoryEntry.EVENT_COMP_INV_BY_NAME, current_user.id)
    db.session.add(hEntry)
    resp = flask.jsonify({'status': status['status_code'], 'message': status['text']})
    resp.status_code = status['status_code']
    return resp;


@bp.route("/fleet/members/", methods=['POST'])
@login_required
@perm_management.require(http_exception=401)
def invite_to_fleet():
    characterID = int(request.form.get('charID'))
    waitlistID = int(request.form.get('waitlistID'))
    groupID = int(request.form.get('groupID'))

    character = db.session.query(Character).get(characterID)
    waitlist = db.session.query(Waitlist).filter(Waitlist.id == waitlistID).first();

        # lets check that the given wl exists
    if waitlist is None:
        logger.error("Given waitlist ID=%d is not valid.", waitlistID)
        flask.abort(400)

    squad_type = waitlist.name
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

    if resp.status_code != 204: # invite failed send no notifications
        logger.error("Invited %s by %s into %s failed", character.eve_name, current_user.username, squad_type)
        return resp

    send_notification(characterID, waitlistID)

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
    if resp.status_code == 204:
        spawn_invite_check(characterID, groupID, fleet.fleetID)
    return resp

def dumpclean(obj):
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print k
                dumpclean(v)
            else:
                print '%s : %s' % (k, v)
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                print v
    else:
        print obj

@bp.route("/fleet/movetosafety/", methods=['POST'])
@login_required
@perm_management.require(http_exception=401)
def move_fleetmembers_to_safety():
    fleetID = int(request.form.get('fleetID'))
    crestFleet = db.session.query(CrestFleet).get(fleetID)
    if not crestFleet.comp.get_eve_id() == current_user.get_eve_id():
        flask.abort(403, "You are not the Fleet Comp of this fleet!")
    
    teamspeakID = sget_active_ts_id()
    if teamspeakID is None:
        flask.abort(500, "No TeamSpeak Server set!")
    
    teamspeak = db.session.query(TeamspeakDatum).get(teamspeakID)
    if teamspeak.safetyChannelID is None:
        flask.abort(500, "No TeamSpeak Safety Channel set!")
    
    # get the safety fleet channel id
    member = member_info.get_fleet_members(fleetID, crestFleet.comp)
    for charID in member:
        charname = member[charID].character.name
        move_to_safety_channel(charname, teamspeak.safetyChannelID)
    return make_response("OK", 200)
    