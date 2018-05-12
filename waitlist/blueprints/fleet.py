from typing import Dict, Optional, Any, List

from flask import Response
from flask.blueprints import Blueprint
import logging

from waitlist.permissions import perm_manager
from waitlist.utility import fleet as fleet_utils
from werkzeug.utils import redirect
from flask_login import login_required, current_user
from waitlist import db
from waitlist.storage.database import CrestFleet, WaitlistGroup, SSOToken
from flask.helpers import url_for, make_response
from flask.templating import render_template
from flask.globals import request, session, current_app
import flask
from waitlist.utility.fleet import member_info
from waitlist.blueprints.fc_sso import get_sso_redirect, add_sso_handler
from datetime import datetime
import json
from waitlist.utility.json.fleetdata import FleetMemberEncoder
from waitlist.sso import add_token
from waitlist.utility.manager import OwnerHashCheckManager
from waitlist.utility.outgate.character.info import get_character_fleet_id
from waitlist.utility.swagger import esi_scopes
from waitlist.utility.swagger.eve.fleet import EveFleetEndpoint
from waitlist.utility.swagger.eve.fleet.models import FleetMember

bp = Blueprint('fleet', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('fleet_management')
perm_manager.define_permission('developer_tools')

fleets_manage = perm_manager.get_permission('fleet_management')
perm_dev = perm_manager.get_permission('developer_tools')


@login_required
@fleets_manage.require(http_exception=401)
def handle_new_fleet_token(tokens):
    add_token(tokens)
    return redirect(url_for('fleet.take_over_fleet'))


'''
register sso handler
'''
add_sso_handler('get_fleet_token', handle_new_fleet_token)

'''
Steps:
    url == process the url and setup quads/motd if wanted
    selection == select which squads to invite too
'''


@bp.route("/setup/<string:step>", methods=['POST'])
@login_required
@fleets_manage.require(http_exception=401)
def setup_steps(step: str) -> Any:
    if step == 'url':
        return setup_step_url()
    elif step == "select":
        return setup_step_select()
    pass


def setup_step_url():
    token: Optional[SSOToken] = current_user.get_a_sso_token_with_scopes(esi_scopes.fleetcomp_scopes)
    if token is None:
        return Response('You have no api token with the required scopes associated with your account,'
                        ' please take over the fleet again.',
                        status=412)
    skip_setup = request.form.get('skip-setup')
    try:
        fleet_id: int = int(request.form.get('fleet-id'))
    except ValueError:
        flask.flash(f"fleet-id={request.form.get('fleet-id')} was not valid.", "danger")
        return redirect(url_for('fleetoptions.fleet'))
    fleet_type = request.form.get('fleet-type')
    if skip_setup == "no-setup":
        skip_setup = True
    else:
        skip_setup = False

    if not skip_setup:
        fleet_utils.setup(token, fleet_id, fleet_type)

    return get_select_form(token, fleet_id)


def get_select_form(token: SSOToken, fleet_id: int) -> Any:
    fleet_api = EveFleetEndpoint(token, fleet_id)
    wings = fleet_api.get_wings()
    if wings.is_error():
        logger.error(f"Could not get wings for fleet_id[{fleet_id}], maybe some ones tokens are wrong. {wings.error()}")
        flask.abort(wings.code(), wings.error())

    groups = db.session.query(WaitlistGroup).all()
    auto_assign = {}

    for wing in wings.wings():
        for squad in wing.squads():
            lname = squad.name().lower()
            if "logi" in lname:
                auto_assign['logi'] = squad
            elif "sniper" in lname:
                auto_assign['sniper'] = squad
            elif "dps" in lname and "more" not in lname:
                auto_assign['dps'] = squad
            elif ("dps" in lname and "more" in lname) or "other" in lname:
                auto_assign['overflow'] = squad
    return render_template("fleet/setup/select.html", wings=wings.wings(), fleet_id=fleet_id,
                           groups=groups, assign=auto_assign)


def setup_step_select() -> Optional[Response]:
    logi_s = request.form.get('wl-logi')
    sniper_s = request.form.get('wl-sniper')
    dps_s = request.form.get('wl-dps')
    overflow_s = request.form.get('wl-overflow')
    try:
        fleet_id = int(request.form.get('fleet-id'))
    except ValueError:
        flask.abort(400, "No valid fleet-id given!")
        return None

    try:
        group_id = int(request.form.get('fleet-group'))
    except ValueError:
        flask.abort(400, "No valid fleet-group-id given!")
        return None

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
        fleet.groupID = group_id
        fleet.compID = current_user.id
        oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
        if oldfleet is not None:
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
        fleet.groupID = group_id
        if fleet.compID != current_user.id:
            oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
            if oldfleet is not None:
                oldfleet.compID = None
            fleet.compID = current_user.id

    db.session.commit()
    with open("set_history.log", "a+") as f:
        f.write('{} - {} is taking a fleet on CREST\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                              fleet.comp.username))
    return redirect(url_for('index'))


@bp.route("/setup/change_squads/<fleet_id>", methods=["GET"])
@login_required
@fleets_manage.require()
def change_setup(fleet_id):
    return get_select_form(fleet_id)


@bp.route("/pffleet/<int:fleetid>")
@login_required
@perm_dev.require(http_exception=401)
def print_fleet(fleetid: int) -> Response:
    cached_members = member_info.get_cache_data(fleetid)
    if cached_members is None:
        crest_fleet = db.session.query(CrestFleet).get(fleetid)
        members: Dict[int, FleetMember] = member_info.get_fleet_members(fleetid, crest_fleet.comp)
        if members is None:
            return make_response("No cached or new info")
        cached_members = members
    return current_app.response_class(
        json.dumps(cached_members, indent=None if request.is_xhr else 2, cls=FleetMemberEncoder),
        mimetype='application/json')


@bp.route("/take", methods=["GET"])
@login_required
@fleets_manage.require()
def take_over_fleet():
    # lets make sure we got the token we need

    token: SSOToken = current_user.get_a_sso_token_with_scopes(esi_scopes.fleetcomp_scopes)
    if token is None:
        # if not, get it. And then return here
        return get_sso_redirect('get_fleet_token', ' '.join(esi_scopes.fleetcomp_scopes))

    fleet_id = get_character_fleet_id(token, current_user.get_eve_id())
    if fleet_id is None:
        flask.flash("You are not in a fleet, or didn't not provide rights to read them.", "danger")
        return redirect(url_for("fleetoptions.fleet"))
    fleet = db.session.query(CrestFleet).get(fleet_id)

    if fleet is None:
        # we don't have a setup fleet
        # this is the fleetsetup page
        return render_template("fleet/setup/fleet_url.html", fleetID=fleet_id)
    else:
        # if we got a fleet
        # lets remove the current use from a fleet he might be assigned too
        # and assign him as the new fleets comp
        if fleet.compID != current_user.id:
            oldfleet = db.session.query(CrestFleet).filter((CrestFleet.compID == current_user.id)).first()
            if oldfleet is not None:
                oldfleet.compID = None
            fleet.compID = current_user.id
            db.session.commit()
            with open("set_history.log", "a+") as f:
                f.write('{} - {} is taking a fleet on CREST\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                                      fleet.comp.username))
    return redirect(url_for('fleetoptions.fleet'))


@bp.route("/<int:fleet_id>/change-type", methods=['GET'])
@login_required
@fleets_manage.require()
def change_type(fleet_id: int) -> Any:
    groups = db.session.query(WaitlistGroup).all()
    return render_template("fleet/takeover/change-group-form.html", fleetID=fleet_id, groups=groups)


@bp.route("/<int:fleet_id>/change-type", methods=['POST'])
@login_required
@fleets_manage.require()
def change_type_submit(fleet_id: int) -> Any:
    fleet_group = int(request.form.get('fleet-group'))
    fleet = db.session.query(CrestFleet).get(fleet_id)
    if fleet is None:
        flask.abort(404)

    fleet.groupID = fleet_group
    db.session.commit()
    return redirect(url_for("fleetoptions.fleet"))
