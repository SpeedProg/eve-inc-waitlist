from flask.blueprints import Blueprint
import logging
from waitlist.data.perm import perm_management, perm_dev
from waitlist.utility import fleet as fleetUtils
from werkzeug.utils import redirect
from flask_login import login_required, current_user
from waitlist.base import db
from waitlist.storage.database import CrestFleet, WaitlistGroup
from waitlist.utility.config import crest_client_id, crest_client_secret
from pycrest.eve import AuthedConnectionB
from flask.helpers import url_for
from flask.templating import render_template
from flask.globals import request, session
import re
import flask
from waitlist.utility.fleet import get_wings
from waitlist.utility.crest import create_token_cb
from waitlist.blueprints.fc_sso import get_sso_redirect
from pycrest.errors import APIException

bp = Blueprint('fleet', __name__)
logger = logging.getLogger(__name__)

'''
Setps:
    url == process the url and setup quads/motd if wanted
    selection == select which squads to invite too
'''
@bp.route("/setup/<string:step>", methods=['POST'])
@login_required
@perm_management.require(http_exception=401)
def setup_steps(step):
    if step == 'url':
        return setup_step_url()
    elif step == "select":
        return setup_step_select()
    pass

def setup_step_url():
    skip_setup = request.form.get('skip-setup')
    fleet_link = request.form.get('fleet-link')
    fleet_type = request.form.get('fleet-type')
    if skip_setup == "no-setup":
        skip_setup = True
    else:
        skip_setup = False
    
    fleet_id_search = re.search('https://crest-tq.eveonline.com/fleets/(\d+)/', fleet_link, re.IGNORECASE)
    fleet_id = None
    if fleet_id_search:
        fleet_id = int(fleet_id_search.group(1))
    
    if fleet_id is None:
        flask.abort(400)
    
    if not skip_setup:
        try:
            fleetUtils.setup(fleet_id, fleet_type)
        except APIException as ex:
            flask.abort(409, "Failed to setup fleet. You may not own this fleet. " + str(ex))
    
    return get_select_form(fleet_id)

def get_select_form(fleet_id):
    try:
        wings = get_wings(fleet_id)
    except APIException as ex:
            flask.abort(409, "Failed to setup fleet. You may not own this fleet. " + str(ex))
    active_groups = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True)
    auto_assign = {}
    

    for wing in wings:
        for squad in wing.squadsList:
            lname = squad.name.lower()
            if "logi" in lname:
                auto_assign['logi'] = squad
            elif "sniper" in lname:
                auto_assign['sniper'] = squad
            elif "dps" in lname and not "more" in lname:
                auto_assign['dps'] = squad
            elif ("dps" in lname and "more" in lname) or "other" in lname:
                auto_assign['overflow'] = squad
    return render_template("/fleet/setup/select.html", wings=wings, fleet_id=fleet_id, groups=active_groups, assign=auto_assign)

def setup_step_select():
    logi_s = request.form.get('wl-logi')
    sniper_s = request.form.get('wl-sniper')
    dps_s = request.form.get('wl-dps')
    overflow_s = request.form.get('wl-overflow')
    try:
        fleet_id = int(request.form.get('fleet-id'))
    except ValueError:
        flask.abort(400, "No valid fleet-id given!")
    try:
        groupID = int(request.form.get('fleet-group'))
    except:
        flask.abort(400, "No valid fleet-group-id given!")
    # create [wingID, squadID] lists
    logi = [int(x) for x in logi_s.split(';')]
    sniper = [int(x) for x in sniper_s.split(';')]
    dps = [int(x) for x in dps_s.split(';')]
    overflow = [int(x) for x in overflow_s.split(';')]
    
    fleet = db.session.query(CrestFleet).get(fleet_id)
    if fleet is None:
        fleet = CrestFleet()
        fleet.fleetID = fleet_id
        fleet.logiWingID = logi[0]
        fleet.logiSquadID = logi[1]
        fleet.sniperWingID = sniper[0]
        fleet.sniperSquadID = sniper[1]
        fleet.dpsWingID = dps[0]
        fleet.dpsSquadID = dps[1]
        fleet.otherWingID = overflow[0]
        fleet.otherSquadID = overflow[1]
        fleet.groupID = groupID
        fleet.compID = current_user.id
        oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
        if oldfleet != None:
            oldfleet.compID = None
        db.session.add(fleet)
    else:
        fleet.logiWingID = logi[0]
        fleet.logiSquadID = logi[1]
        fleet.sniperWingID = sniper[0]
        fleet.sniperSquadID = sniper[1]
        fleet.dpsWingID = dps[0]
        fleet.dpsSquadID = dps[1]
        fleet.otherWingID = overflow[0]
        fleet.otherSquadID = overflow[1]
        fleet.groupID = groupID
        if fleet.compID != current_user.id:
            oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
            if oldfleet != None:
                oldfleet.compID = None
            fleet.compID = current_user.id

    db.session.commit()
    return redirect(url_for('index'))

@bp.route("/setup/change_squads/<int:fleetID>", methods=["GET"])
@login_required
@perm_management.require()
def change_setup(fleetID):
    return get_select_form(fleetID)

@bp.route("/setup/", methods=['GET'])
@login_required
@perm_management.require(http_exception=401)
def setup_start():
    return render_template("/fleet/setup/fleet_url.html")

@bp.route("/setup/<int:fleet_id>", methods=['GET'])
@login_required
@perm_management.require(http_exception=401)
def setup(fleet_id):
    (logiID, sniperID, dpsID, moreDpsID) = fleetUtils.setup(fleet_id)
    fleet = db.session.query(CrestFleet).get(fleet_id)
    if fleet is None:
        fleet = CrestFleet()
        fleet.id = fleet_id
        fleet.logiSquadID = logiID
        fleet.sniperSquadID = sniperID
        fleet.dpsSquadID = dpsID
        fleet.otherSquadID = moreDpsID
        db.session.add(fleet)
    else:
        fleet.logiSquadID = logiID
        fleet.sniperSquadID = sniperID
        fleet.dpsSquadID = dpsID
        fleet.otherSquadID = moreDpsID

    current_user.fleet = fleet
    db.session.commit()
    return redirect(url_for('settings.fleet'))

@bp.route("/pffleet/<int:fleetid>")
@login_required
@perm_dev.require(http_exception=401)
def print_fleet(fleetid):
    fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleetid)+"/"
    data = {
            'access_token': current_user.access_token,
            'refresh_token': current_user.refresh_token,
            'expires_in': current_user.access_token_expires
            }
    fleet = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(current_user.id))
    return str(fleet().wings())

@bp.route("/take", methods=['GET'])
@login_required
@perm_management.require(http_exception=401)
def take_form():
    return render_template("/fleet/takeover/link-form.html")

@bp.route("/take", methods=["POST"])
@login_required
@perm_management.require()
def take_link():
    link = request.form.get('fleet-link')
    fleet_id_search = re.search('https://crest-tq.eveonline.com/fleets/(\d+)/', link, re.IGNORECASE)
    fleet_id = None
    if fleet_id_search:
        fleet_id = int(fleet_id_search.group(1))
    
    if fleet_id is None:
        flask.abort(400)
    
    fleet = db.session.query(CrestFleet).get(fleet_id)

    if fleet is None:
        return get_sso_redirect("setup")
    elif current_user.refresh_token is None:
        session['fleet_id'] = fleet_id
        return get_sso_redirect("takeover")
    else:
        if fleet.compID != current_user.id:
            oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
            if oldfleet != None:
                oldfleet.compID = None
            fleet.compID = current_user.id
            db.session.commit()
    return redirect(url_for('settings.fleet'))

@bp.route('/take_sso', methods=['GET'])
@login_required
@perm_management.require()
def takeover_sso_cb():
    if not('fleet_id' in session):
        flask.abort(400)
    
    fleet_id = session['fleet_id']
    fleet = db.session.query(CrestFleet).get(fleet_id)
    if fleet.compID != current_user.id:
        oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
        if oldfleet != None:
            oldfleet.compID = None
        fleet.compID = current_user.id
        db.session.commit()
    return redirect(url_for('settings.fleet'))

@bp.route("/<int:fleetID>/change-type", methods=['GET'])
@login_required
@perm_management.require()
def change_type(fleetID):
    active_groups = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True)
    return render_template("/fleet/takeover/change-group-form.html", fleetID=fleetID, groups=active_groups)

@bp.route("/<int:fleetID>/change-type", methods=['POST'])
@login_required
@perm_management.require()
def change_type_submit(fleetID):
    fleetGroup = int(request.form.get('fleet-group'))
    fleet = db.session.query(CrestFleet).get(fleetID)
    if fleet is None:
        flask.abort(404)
    
    fleet.groupID = fleetGroup
    db.session.commit()
    return redirect(url_for("settings.fleet"))