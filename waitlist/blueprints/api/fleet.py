from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
import flask
from flask.globals import request

from waitlist.permissions import perm_manager
from waitlist.storage.database import CrestFleet, Waitlist, \
    Character, WaitlistEntry, HistoryEntry, HistoryExtInvite, \
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
from waitlist.utility.settings import sget_active_ts_id
from flask_babel import gettext

bp = Blueprint('api_fleet', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('fleet_management')

perm_fleet_manage = perm_manager.get_permission('fleet_management')


@bp.route("/<int:fleet_id>/", methods=["DELETE"])
@login_required
@perm_fleet_manage.require(http_exception=401)
def remove_fleet(fleet_id: int):
    logger.info("%s deletes crest fleet %i", current_user.username, fleet_id)
    db.session.query(CrestFleet).filter(CrestFleet.fleetID == fleet_id).delete()
    db.session.commit()
    return flask.jsonify(status_code=200, message="Fleet Deleted")


@bp.route("/fleet/actions/invite/<string:name>", methods=['POST'])
@login_required
@perm_fleet_manage.require()
def fleet_actions_invite(name: str):
    character = get_character_by_name(name)
    fleet = current_user.fleet

    if fleet is None:
        logger.info("%s tried to invite someone by name while he has no fleet",
                    current_user)
        flask.abort(428, gettext('You are not associated with a fleet!'))

    if character is None:
        logger.info('%s tried to inviate character with name=%s who does not exist.',
                    current_user,
                    name)
        flask.abort(400,
                    gettext('The character you tried to invite could not be found!'))

    logger.info("%s invites %s by name to fleet %d", current_user.username,
                name, fleet.fleetID)
    status = invite(character.id, [(fleet.dpsWingID, fleet.dpsSquadID),
                                   (fleet.otherWingID, fleet.otherSquadID),
                                   (fleet.sniperWingID, fleet.sniperSquadID),
                                   (fleet.logiWingID, fleet.logiSquadID)])
    h_entry = create_history_object(character.get_eve_id(),
                                    HistoryEntry.EVENT_COMP_INV_BY_NAME,
                                    current_user.id)
    db.session.add(h_entry)
    resp = flask.jsonify({'status': status['status_code'],
                          'message': status['text']})
    resp.status_code = status['status_code']
    return resp


@bp.route("/fleet/members/", methods=['POST'])
@login_required
@perm_fleet_manage.require(http_exception=401)
def invite_to_fleet():
    character_id = int(request.form.get('charID'))
    waitlist_id = int(request.form.get('waitlistID'))
    group_id = int(request.form.get('groupID'))

    character = db.session.query(Character).get(character_id)
    waitlist = db.session.query(Waitlist).filter(Waitlist.id == waitlist_id).first()

    # lets check that the given wl exists
    if waitlist is None:
        logger.error("Given waitlist ID=%d is not valid.", waitlist_id)
        resp = jsonify(status_code=428,
                       message=gettext('Given waitlist ID=%(waitlist_id)d is not valid.',
                                       waitlist_id=waitlist_id))
        resp.status_code = 428
        return resp

    squad_type = waitlist.name
    logger.info("Invited %s by %s into %s", character.eve_name, current_user.username, squad_type)
    if current_user.fleet is None:
        logger.info("%s is currently not not boss of a fleet, he can't invite people.", current_user.username)
        resp = jsonify(status_code=409,
                       message=gettext('You are not currently Boss of a Fleet'))
        resp.status_code = 409
        return resp
    fleet = current_user.fleet

    # generate a list in which order squads should be preferred in case the main squad is full
    if squad_type == "logi":
        squad_id_list = [(fleet.logiWingID, fleet.logiSquadID), (fleet.otherWingID, fleet.otherSquadID),
                         (fleet.sniperWingID, fleet.sniperSquadID), (fleet.dpsWingID, fleet.dpsSquadID)]
    elif squad_type == "dps":
        squad_id_list = [(fleet.dpsWingID, fleet.dpsSquadID), (fleet.otherWingID, fleet.otherSquadID),
                         (fleet.sniperWingID, fleet.sniperSquadID), (fleet.logiWingID, fleet.logiSquadID)]
    elif squad_type == "sniper":
        squad_id_list = [(fleet.sniperWingID, fleet.sniperSquadID), (fleet.otherWingID, fleet.otherSquadID),
                         (fleet.dpsWingID, fleet.dpsSquadID), (fleet.logiWingID, fleet.logiSquadID)]
    else:
        return Response(flask.jsonify({'message': gettext('Unknown Squad Type')}), 415)

    # invite over crest and get back the status
    status = invite(character_id, squad_id_list)

    if status['status_code'] != 204:
        resp = jsonify({'status': status['status_code'], 'message': status['text']})
        resp.status_code = status['status_code']
    else:
        logger.info("Creating empty content response")
        resp = make_response('', 204)

    if resp.status_code != 204:  # invite failed send no notifications
        if resp.status_code != 520:
            logger.error("Invited %s by %s into %s failed, status_code %s message %s",
                         character.eve_name, current_user.username, squad_type,
                         resp.status_code, status['text'])
        return resp

    send_notification(character_id, waitlist_id)

    h_entry = create_history_object(character.get_eve_id(), HistoryEntry.EVENT_COMP_INV_PL, current_user.id)
    h_entry.exref = waitlist.group.groupID

    # create a invite history extension
    # get wl entry for creation time
    wl_entry = db.session.query(WaitlistEntry) \
        .filter((WaitlistEntry.waitlist_id == waitlist_id) & (WaitlistEntry.user == character_id)).first()
    if wl_entry is None:
        logger.error("Waitlist Entry with ID=%d does not exist!", waitlist_id)
        return resp

    db.session.add(h_entry)
    db.session.flush()
    db.session.refresh(h_entry)

    history_ext = HistoryExtInvite()
    history_ext.historyID = h_entry.historyID
    history_ext.waitlistID = waitlist_id
    history_ext.timeCreated = wl_entry.creation
    history_ext.timeInvited = datetime.utcnow()
    db.session.add(history_ext)

    db.session.commit()
    logger.info("%s invited %s to fleet from %s.", current_user.username, character.eve_name, waitlist.group.groupName)

    # set a timer for 1min and 6s that checks if the person accepted the invite
    logger.debug("API Response for %s was %d", character.eve_name, resp.status_code)
    if resp.status_code == 204:
        try:
            spawn_invite_check(character_id, group_id, fleet.fleetID)
        except Exception:
            logger.exception('Failed to spawn invite check')
    else:
        logger.debug(f"Did not get 204 status, instead got {resp.status_code} no invite check spawned")

    return resp


@bp.route("/fleet/movetosafety/", methods=['POST'])
@login_required
@perm_fleet_manage.require(http_exception=401)
def move_fleetmembers_to_safety():
    fleet_id = int(request.form.get('fleetID'))
    crest_fleet = db.session.query(CrestFleet).get(fleet_id)
    if not crest_fleet.comp.get_eve_id() == current_user.get_eve_id():
        flask.abort(403, "You are not the Fleet Comp of this fleet!")

    teamspeak_id = sget_active_ts_id()
    if teamspeak_id is None:
        flask.abort(500, "No TeamSpeak Server set!")

    teamspeak: TeamspeakDatum = db.session.query(TeamspeakDatum).get(teamspeak_id)
    if teamspeak.safetyChannelID is None:
        flask.abort(500, "No TeamSpeak Safety Channel set!")

    # get the safety fleet channel id
    member = member_info.get_fleet_members(fleet_id, crest_fleet.comp)
    for charID in member:
        char_id: int = member[charID].character_id()
        char = db.session.query(Character).get(char_id)
        if char is None:
            continue
        safety_channel_id: int = teamspeak.safetyChannelID
        move_to_safety_channel(char.eve_name, safety_channel_id)
    return make_response("OK", 200)
