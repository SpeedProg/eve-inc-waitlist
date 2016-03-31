from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from waitlist import db
from waitlist.storage.database import Waitlist
from flask import jsonify
from waitlist.data.perm import perm_management
wl_api = Blueprint('waitlist_api', __name__)
logger = logging.getLogger(__name__)

def makeJsonWLEntry(entry):
    return {
            'id': entry.id,
            'character': makeJsonCharacter(entry.user_data),
            'fittings': makeJsonFittings(entry.fittings)
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
            'dna': dbfitting.get_dna()
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
    jsonwls = []
    waitlists = db.session.query(Waitlist).all();
    for wl in waitlists:
        jsonwls.append(makeJsonWL(wl))
    
    return jsonify(waitlists=jsonwls)
