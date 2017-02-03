from flask.blueprints import Blueprint
import logging
from waitlist.data.perm import perm_management, perm_dev
from waitlist.utility import fleet as fleetUtils
from werkzeug.utils import redirect
from flask_login import login_required, current_user
from waitlist.base import db
from waitlist.storage.database import CrestFleet, WaitlistGroup, SSOToken,\
    EveApiScope
from waitlist.utility.config import crest_client_id, crest_client_secret
from flask.helpers import url_for
from flask.templating import render_template
from flask.globals import request, session, current_app
import re
import flask
from waitlist.utility.fleet import member_info
from waitlist.blueprints.fc_sso import get_sso_redirect, add_sso_handler
from datetime import datetime
from datetime import timedelta
import requests
import base64
from sqlalchemy import or_
import json
from waitlist.utility.json.fleetdata import FleetMemberEncoder
from waitlist.sso import whoAmI
from waitlist.utility.swagger.eve.fleet import EveFleetEndpoint
from waitlist.utility.utils import token_has_scopes

bp = Blueprint('fleet', __name__)
logger = logging.getLogger(__name__)


'''
SSO cb handler
'''
@login_required
def handle_token_update(code):
    header = {'Authorization': 'Basic '+base64.b64encode(crest_client_id+":"+crest_client_secret),
              'Content-Type': 'application/x-www-form-urlencoded',
              'Host': 'login.eveonline.com'}
    params = {'grant_type': 'authorization_code',
              'code': code}
    r = requests.post("https://login.eveonline.com/oauth/token", headers=header, params=params)
    tokens = r.json()
    re_token = tokens['refresh_token']
    acc_token = tokens['access_token']
    exp_in = int(tokens['expires_in'])
    
    authInfo = whoAmI(acc_token)
    charName = authInfo['CharacterName']
    if charName != current_user.get_eve_name():
        flask.abort(409, 'You did not grant authorization for the right character "'+current_user.get_eve_name()+'". Instead you granted it for "'+charName+'"')

    scopenames = authInfo['Scopes'].split(' ')
    if (current_user.ssoToken == None):
        ssoToken = SSOToken(refresh_token = re_token, access_token = acc_token, access_token_expires = datetime.utcnow() + timedelta(seconds=exp_in))
        current_user.ssoToken = ssoToken
        dbscopes = db.session.query(EveApiScope).filter(or_( EveApiScope.scopeName == name for name in scopenames ))
        for dbscope in dbscopes:
            current_user.ssoToken.scopes.append(dbscope)
    else:
        current_user.ssoToken.refresh_token = re_token
        current_user.ssoToken.access_token = acc_token
        current_user.ssoToken.access_token_expires = datetime.utcnow() + timedelta(seconds=exp_in)
        for dbscope in current_user.ssoToken.scopes:
            current_user.ssoToken.scopes.remove(dbscope)
        dbscopes = db.session.query(EveApiScope).filter(or_( EveApiScope.scopeName == name for name in scopenames ))
        for dbscope in dbscopes:
            current_user.ssoToken.scopes.append(dbscope)
            
    db.session.commit()

@login_required
@perm_management.require(http_exception=401)
def handle_setup_start_sso_cb(tokens):
    handle_token_update(tokens)
    return redirect(url_for("fleet.setup_start"))

@login_required
@perm_management.require(http_exception=401)
def handle_takeover_sso_cb(tokens):
    handle_token_update(tokens)
    return redirect(url_for('fleet.takeover_sso_cb'))


'''
register sso handler
'''
add_sso_handler('setup', handle_setup_start_sso_cb)
add_sso_handler("takeover", handle_takeover_sso_cb)

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
        fleetUtils.setup(fleet_id, fleet_type)
    
    return get_select_form(fleet_id)

def get_select_form(fleet_id):
    # type: (int) -> None
    fleetApi = EveFleetEndpoint(fleet_id)
    wings = fleetApi.get_wings()
    if wings.is_error():
        logger.error("Could not get wings for fleetID[%d], maybe some ones tokes are wrong", fleet_id)
        flask.abort(500)

    groups = db.session.query(WaitlistGroup).all()
    auto_assign = {}

    for wing in wings.wings():
        for squad in wing.squads():
            lname = squad.name().lower()
            if "logi" in lname:
                auto_assign['logi'] = squad
            elif "sniper" in lname:
                auto_assign['sniper'] = squad
            elif "dps" in lname and not "more" in lname:
                auto_assign['dps'] = squad
            elif ("dps" in lname and "more" in lname) or "other" in lname:
                auto_assign['overflow'] = squad
    return render_template("/fleet/setup/select.html", wings=wings.wings(), fleet_id=fleet_id, groups=groups, assign=auto_assign)

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
    with open("set_history.log", "a+") as f:
        f.write('{} - {} is taking a fleet on CREST\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), fleet.comp.username))
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
    fleet_id = session['fleet_id']
    return render_template("/fleet/setup/fleet_url.html", fleetID=fleet_id)

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
    with open("set_history.log", "a+") as f:
        f.write('{} - {} is taking a fleet on CREST\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), fleet.comp.username))

    db.session.commit()
    return redirect(url_for('settings.fleet'))

@bp.route("/pffleet/<int:fleetid>")
@login_required
@perm_dev.require(http_exception=401)
def print_fleet(fleetid):
    cachedMembers = member_info.get_cache_data(fleetid)
    if (cachedMembers == None):
        crestFleet = db.session.query(CrestFleet).get(fleetid)
        members = member_info.get_fleet_members(fleetid, crestFleet.comp)
        if (members == None):
            return "No cached or new info"
        cachedMembers = members.FleetMember()
    return current_app.response_class(json.dumps(cachedMembers,
        indent=None if request.is_xhr else 2, cls=FleetMemberEncoder), mimetype='application/json')

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
        session['fleet_id'] = fleet_id
        return get_sso_redirect("setup", 'esi-fleets.read_fleet.v1 esi-fleets.write_fleet.v1 esi-mail.send_mail.v1 esi-ui.open_window.v1')
    elif current_user.ssoToken is None or current_user.ssoToken.refresh_token is None:
        session['fleet_id'] = fleet_id
        return get_sso_redirect("takeover", 'esi-fleets.read_fleet.v1 esi-fleets.write_fleet.v1 esi-mail.send_mail.v1 esi-ui.open_window.v1')
    else:
        # make sure the token we have has all the scopes we need!
        if not token_has_scopes(current_user.ssoToken, ['esi-fleets.read_fleet.v1', 'esi-fleets.write_fleet.v1', 'esi-ui.open_window.v1']):
            session['fleet_id'] = fleet_id
            return get_sso_redirect("takeover", 'esi-fleets.read_fleet.v1 esi-fleets.write_fleet.v1 esi-mail.send_mail.v1 esi-ui.open_window.v1')
        if fleet.compID != current_user.id:
            oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
            if oldfleet != None:
                oldfleet.compID = None
            fleet.compID = current_user.id
            db.session.commit()
            with open("set_history.log", "a+") as f:
                f.write('{} - {} is taking a fleet on CREST\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), fleet.comp.username))
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
        with open("set_history.log", "a+") as f:
            f.write('{} - {} is taking a fleet on CREST\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), fleet.comp.username))
    return redirect(url_for('settings.fleet'))

@bp.route("/<int:fleetID>/change-type", methods=['GET'])
@login_required
@perm_management.require()
def change_type(fleetID):
    groups = db.session.query(WaitlistGroup).all()
    return render_template("/fleet/takeover/change-group-form.html", fleetID=fleetID, groups=groups)

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