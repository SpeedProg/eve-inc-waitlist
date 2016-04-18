from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from waitlist import db
from waitlist.storage.database import WaitlistGroup, HistoryEntry
from flask import jsonify
from waitlist.data.perm import perm_management, perm_officer, perm_leadership
from flask.globals import request
from datetime import datetime
import time
wl_api = Blueprint('waitlist_api', __name__)
logger = logging.getLogger(__name__)

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
@perm_management.require(http_exception=401)
def history_since():
    laststamp = int(request.args.get('last'))
    logger.info("last=%s", str(laststamp))
    since = datetime.utcfromtimestamp(laststamp / 1000.0)
    logger.info("Looking for %s", str(since))
    tnow = datetime.utcnow()
    if not (perm_officer.can() or perm_leadership.can()):
        maxTime = datetime.timedelta(minutes=240)
        if tnow - since > datetime.timedelta(minutes=240) :
            since = tnow - maxTime

    newHistoryEntries = db.session.query(HistoryEntry).filter(HistoryEntry.time > since).all()
    
    return jsonify(makeHistoryJson(newHistoryEntries))
    
