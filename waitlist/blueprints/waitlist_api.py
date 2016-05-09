from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist import db
from waitlist.storage.database import WaitlistGroup, HistoryEntry, Character,\
    WaitlistEntry, HistoryExtInvite, Waitlist, CrestFleet
from flask import jsonify
from waitlist.data.perm import perm_management, perm_officer, perm_leadership,\
    perm_comphistory
from flask.globals import request
from datetime import datetime, timedelta
import flask
from waitlist.utility.crest.fleet import invite, connection_cache
from waitlist.data.sse import InviteEvent
from waitlist.blueprints import send_invite_notice
from waitlist.utility.history_utils import create_history_object
from threading import Timer
wl_api = Blueprint('waitlist_api', __name__)
logger = logging.getLogger(__name__)

class FleetMemberInfo():
    def __init__(self):
        self._lastupdate = {}
        self._lastmembers = {}
    
    def get_fleet_members(self, fleetID, account):
        return self.get_data(fleetID, account)
    
    def _json_to_members(self, json):
        data = {}
        for member in json.items:
            data[member.character.id] = member
        return data
    
    def get_data(self, fleetID, account):
        utcnow = datetime.utcnow()
        if (self.is_expired(fleetID, utcnow)):
            fleet = connection_cache.get_connection(fleetID, account)
            json = fleet().members()
            self.update_cache(fleetID, utcnow, self._json_to_members(json))
        
        return self._lastmembers[fleetID]
    
    def is_expired(self, fleetID, utcnow):
        if not fleetID in self._lastupdate:
            return True
        else:
            lastUpdated = self._lastupdate[fleetID]
            if utcnow - lastUpdated < timedelta(seconds=5):
                return False
            else:
                return True
    
    def update_cache(self, fleetID, utcnow, data):
        self._lastmembers[fleetID] = data
        self._lastupdate[fleetID] = utcnow

member_info = FleetMemberInfo()

def makeJsonWLEntry(entry):
    return {
            'id': entry.id,
            'character': makeJsonCharacter(entry.user_data),
            'fittings': makeJsonFittings(entry.fittings),
            'time': entry.creation
            }

def makeJsonWL(dbwl):
    return {
            'id': dbwl.id,
            'name': dbwl.name,
            'entries': makeEntries(dbwl.entries)
    }

def makeJsonCharacter(dbcharacter):
    return {
            'id': dbcharacter.get_eve_id(),
            'name': dbcharacter.get_eve_name(),
            'newbro': dbcharacter.is_new()
            }

def makeJsonFitting(dbfitting):
    return {
            'id': dbfitting.id,
            'shipType': dbfitting.ship_type,
            'shipName': dbfitting.ship.typeName,
            'modules': dbfitting.modules,
            'comment': dbfitting.comment,
            'dna': dbfitting.get_dna(),
            'wl_type': dbfitting.wl_type
        }

def makeJsonFittings(dbfittings):
    fittings = []
    for fit in dbfittings:
        fittings.append(makeJsonFitting(fit))

    return fittings

def makeEntries(dbentries):
    entries = []
    for entry in dbentries:
        entries.append(makeJsonWLEntry(entry))
    return entries

@wl_api.route("/waitlists/", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def waitlist():
    group_id = int(request.args.get('group'))
    jsonwls = []
    group = db.session.query(WaitlistGroup).get(group_id)
    waitlists = [group.xuplist, group.logilist, group.dpslist, group.sniperlist]
    if group.otherlist is not None:
        waitlists.append(group.otherlist)

    for wl in waitlists:
        jsonwls.append(makeJsonWL(wl))
    
    return jsonify(waitlists=jsonwls, groupName=group.groupName, groupID=group.groupID, displayName=group.displayName)

def check_invited(fleetID):
    member_info.get_fleet_members(fleetID, current_user)

def makeHistoryJson(entries):
    return {'history': [makeHistoryEntryJson(entry) for entry in entries]}

def makeHistoryEntryJson(entry):
    return {'historyID': entry.historyID,
    'action': entry.action,
    'time': entry.time,
    'exref': entry.exref,
    'fittings': [makeJsonFitting(fit) for fit in entry.fittings],
    'source': None if entry.source is None else makeJsonAccount(entry.source),
    'target': makeJsonCharacter(entry.target)
    }

def makeJsonAccount(acc):
    return {'id': acc.id,
            'character': makeJsonCharacter(acc.current_char_obj),
            'username': acc.username,
    }

@wl_api.route("/history/since", methods=["GET"])
@login_required
@perm_comphistory.require(http_exception=401)
def history_since():
    laststamp = int(request.args.get('last'))
    logger.info("last=%s", str(laststamp))
    since = datetime.utcfromtimestamp(laststamp / 1000.0)
    logger.info("Looking for %s", str(since))
    tnow = datetime.utcnow()
    if not (perm_officer.can() or perm_leadership.can()):
        maxTime = timedelta(minutes=240)
        if tnow - since > maxTime:
            since = tnow - maxTime

    newHistoryEntries = db.session.query(HistoryEntry).filter(HistoryEntry.time > since).all()
    
    return jsonify(makeHistoryJson(newHistoryEntries))

@wl_api.route("/fleet/members/", methods=['POST'])
@login_required
@perm_management.require(http_exception=401)
def invite_to_fleet():
    character_id = int(request.form.get('charID'))
    wl_id = int(request.form.get('waitlistID'))
    group_id = int(request.form.get('groupID'))


    if character_id == None:
        logger.error("Tried to send invite to player with no id.")

    waitlist = db.session.query(Waitlist).filter(Waitlist.id == wl_id).first();
    squad_type = waitlist.name
        # lets check that the given wl exists
    if waitlist is None:
        logger.error("Given waitlist id %s is not valid.", str(wl_id))
        flask.abort(400)
    
    group = db.session.query(WaitlistGroup).get(group_id)

    character = db.session.query(Character).get(character_id)
    logger.info("Invited %s by %s into %s", character.eve_name, current_user.username, squad_type)
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
        (flask.jsonify({'message': 'Unknown Squad Type'}), 415)

    # invite over crest and get back the status
    status = invite(character_id, squadIDList)
    
    resp = flask.jsonify({'status': status['status_code'], 'message': status['text']})
    resp.status_code = status['status_code']


    # trigger notification
    event = InviteEvent(character_id)
    send_invite_notice(event)
    #publish(event)
    
    character = db.session.query(Character).filter(Character.id == character_id).first()
    hEntry = create_history_object(character.get_eve_id(), HistoryEntry.EVENT_COMP_INV_PL, current_user.id)
    hEntry.exref = waitlist.group.groupID
    
    # create a invite history extension
    # get wl entry for creation time
    wlEntry = db.session.query(WaitlistEntry).filter((WaitlistEntry.waitlist_id == wl_id) & (WaitlistEntry.user == character_id)).first()
    
    db.session.add(hEntry)
    db.session.flush()
    db.session.refresh(hEntry)
    
    historyExt = HistoryExtInvite()
    historyExt.historyID = hEntry.historyID
    historyExt.waitlistID = wl_id
    historyExt.timeCreated = wlEntry.creation
    historyExt.timeInvited = datetime.utcnow()
    db.session.add(historyExt)

    # get all the entries and increase invite count by 1
    waitlist_entries = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == character_id) &
                                                               ((WaitlistEntry.waitlist_id == group.logiwlID) |
                                                                 (WaitlistEntry.waitlist_id == group.dpswlID) |
                                                                 (WaitlistEntry.waitlist_id == group.sniperwlID))).all()
    
    for entry in waitlist_entries:
        entry.inviteCount += 1
    
    db.session.commit()
    logger.info("%s invited %s to fleet from %s.", current_user.username, character.eve_name, waitlist.group.groupName)
    
    db.session.commit()
    
    # set a timer for 1min and 6s that checks if the person accepted the invite
    t = Timer(66.0,check_invite_and_remove_timer, [character_id, group_id, fleet.fleetID])
    t.start()
    return resp

def check_invite_and_remove_timer(charID, groupID, fleetID):
    group = db.session.query(WaitlistGroup).get(groupID)
    crestFleet = db.session.query(CrestFleet).get(fleetID)
    member = member_info.get_fleet_members(fleetID, crestFleet.comp)
    if charID in member:# he is in the fleet
        waitlist_entries = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) &
                                                           ((WaitlistEntry.waitlist_id == group.logiwlID) |
                                                             (WaitlistEntry.waitlist_id == group.dpswlID) |
                                                             (WaitlistEntry.waitlist_id == group.sniperwlID))).all()
        fittings = []
        for entry in waitlist_entries:
            fittings.extend(entry.fittings)
        
        # check if there is an other waitlist
        if group.otherwlID is not None:
            entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) & (WaitlistEntry.waitlist_id == group.otherwlID)).on_or_none()
            if entry is not None:
                fittings.extend(entry.fittings)
        
        
        waitlist_entries = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) &
                                                                   ((WaitlistEntry.waitlist_id == group.logiwlID) |
                                                                     (WaitlistEntry.waitlist_id == group.dpswlID) |
                                                                     (WaitlistEntry.waitlist_id == group.sniperwlID))).delete()
        # if other waitlist delete those entries too
        if group.otherwlID is not None:
            entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) & (WaitlistEntry.waitlist_id == group.otherwlID)).delete()
        
        hEntry = create_history_object(charID, HistoryEntry.EVENT_AUTO_RM_PL, None, fittings)
        hEntry.exref = group.groupID
        db.session.add(hEntry)
        db.session.commit()
        character = db.session.query(Character).filter(Character.id == charID).first()
        logger.info("auto removed %s from %s waitlist.", character.eve_name, group.groupName)
