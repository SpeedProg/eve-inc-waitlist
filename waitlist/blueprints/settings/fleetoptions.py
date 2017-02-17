import logging
from datetime import datetime

from flask import Response, jsonify
from flask import flash
from flask import redirect
from flask import request
from flask import url_for

from waitlist.blueprints.settings import add_menu_entry
from waitlist.data.sse import StatusChangedSSE
from waitlist.data.sse import send_server_sent_event
from waitlist.permissions import perm_manager
from waitlist.utility import config
from flask import Blueprint
from flask import render_template
from flask_login import current_user, login_required

from waitlist import db
from waitlist.storage.database import WaitlistGroup, Account, IncursionLayout, Station, SolarSystem, Constellation, \
    WaitlistEntry
from waitlist.utility.eve_id_utils import get_constellation, get_system, get_station

bp = Blueprint('fleetoptions', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('fleet_management')
perm_manager.define_permission('fleet_custom_status')
perm_manager.define_permission('fleet_location_edit')

perm_management = perm_manager.get_permission('fleet_management')
perm_custom_status = perm_manager.get_permission('fleet_custom_status')
perm_fleetlocation_edit = perm_manager.get_permission('fleet_location_edit')


@bp.route('/')
@login_required
@perm_management.require(http_exception=401)
def fleet() -> Response:
    groups = db.session.query(WaitlistGroup).all()
    return render_template("settings/fleet.html", user=current_user, groups=groups, scramble=config.scramble_names)


@bp.route("/fleet/status/set/<int:gid>", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def fleet_status_set(gid: int) -> Response:
    action = request.form['action']
    group = db.session.query(WaitlistGroup).get(gid)
    if action == "status":
        text = request.form['status']
        xup = request.form.get('xup', 'off')
        influence = request.form.get('influence')
        influence = False if influence is None else True
        xup_text = "closed"
        if xup == 'off':
            xup = False
        else:
            xup = True
            xup_text = "open"

        if xup != group.enabled:
            group.enabled = xup
            logger.info("XUP was set to %s by %s", xup, current_user.username)

        if influence != group.influence:
            group.influence = influence
            logger.info("Influence setting of grp %s was changed to %s by %s", group.groupID, influence,
                        current_user.username)

        if perm_custom_status.can():
            group.status = text
            logger.info("Status was set to %s by %s", group.status, current_user.username)
            flash("Status was set to " + text + ", xup is " + xup_text, "success")

        else:
            if text == "Running" or text == "Down" or text == "Forming":
                group.status = text
                logger.info("Status was set to %s by %s", group.status, current_user.username)
                flash("Status was set to " + text + ", xup is " + xup_text, "success")
            else:
                logger.info("%s tried to set the status to %s and did not have the rights", current_user.username,
                            group.status)
                flash("You do not have the rights to change the status to " + text, "danger")
                flash("XUP is now " + xup_text, "success")
    elif action == "fc":
        group.fcs.append(current_user)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} sets them self as FC\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                            current_user.username))

        flash("You added your self to FCs " + current_user.get_eve_name(), "success")
    elif action == "manager":
        group.manager.append(current_user)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} sets them self as Fleet Manager\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                                       current_user.username))

        flash("You added your self to manager " + current_user.get_eve_name(), "success")
    elif action == "manager-remove":
        account_id = int(request.form['accountID'])
        account = db.session.query(Account).get(account_id)

        with open("set_history.log", "a+") as f:
            f.write(
                '{} - {} is removed as Fleet Manager by {}\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                                     account.username, current_user.username))

        try:
            group.manager.remove(account)
        except ValueError:
            pass
    elif action == "fc-remove":
        account_id = int(request.form['accountID'])
        account = db.session.query(Account).get(account_id)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} is removed as FC by {}\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                              account.username, current_user.username))

        try:
            group.fcs.remove(account)
        except ValueError:
            pass
    elif action == "add-backseat":
        group.backseats.append(current_user)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} sets them self as Backseat\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                                  current_user.username))

        flash("You added your self as Backseat " + current_user.get_eve_name(), "success")
    elif action == "remove-backseat":
        account_id = int(request.form['accountID'])
        account = db.session.query(Account).get(account_id)
        with open("set_history.log", "a+") as f:
            f.write('{} - {} is removed as Backseat by {}\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                                    account.username, current_user.username))

        try:
            group.backseats.remove(account)
        except ValueError:
            pass

    db.session.commit()

    event = StatusChangedSSE(group)
    send_server_sent_event(event)

    return redirect(url_for(".fleet"), code=303)


@bp.route("/fleet/location/set/<int:gid>", methods=["POST"])
@login_required
@perm_fleetlocation_edit.require(http_exception=401)
def fleet_location_set(gid):
    group = db.session.query(WaitlistGroup).get(gid)
    action = request.form['action']
    if action == "constellation":
        name = request.form['name']
        constellation = get_constellation(name)
        if constellation is None:
            flash("This constellation does not exist! " + name)
            return redirect(url_for(".fleet"), code=303)

        # if we set the constellation look up if we already know dock and hq system
        inc_layout = db.session.query(IncursionLayout).filter(
            IncursionLayout.constellation == constellation.constellationID).first()

        if group.groupName == "default":  # if default waitlist, set all of them
            groups = db.session.query(WaitlistGroup).all()
            logger.info("All Constellations were set to %s by %s", name, current_user.username)
            for group in groups:
                group.constellation = constellation

                # if we know it, set the other information
                if inc_layout is not None:
                    group.system = inc_layout.obj_headquarter
                    logger.info("%s System was autoset to %s by %s for %s", group.groupName,
                                group.system.solarSystemName, current_user.username, group.groupName)
                    group.dockup = inc_layout.obj_dockup
                    logger.info("%s Dock was autoset to %s by %s for %s", group.groupName, group.dockup.stationName,
                                current_user.username, group.groupName)
                else:
                    flash("No Constellation Layout Data found!")
                    group.system = None
                    group.dockup = None

            flash("All Constellations were set to " + name + "!", "success")
        else:  # if not default waitlist set only the single waitlist
            group.constellation = constellation
            logger.info("%s Constellation was set to %s by %s", group.groupName, name, current_user.username)
            # if we set the constellation look up if we already know dock and hq system
            inc_layout = db.session.query(IncursionLayout).filter(
                IncursionLayout.constellation == group.constellation.constellationID).first()
            # if we know it, set the other information
            if inc_layout is not None:
                group.system = inc_layout.obj_headquarter
                logger.info("%s System was autoset to %s by %s", group.groupName, group.system.solarSystemName,
                            current_user.username)
                group.dockup = inc_layout.obj_dockup
                logger.info("%s Dock was autoset to %s by %s", group.groupName, group.dockup.stationName,
                            current_user.username)
            else:
                flash("No Constellation Layout Data found!")
                group.system = None
                group.dockup = None

            flash(group.displayName + " Constellation was set to " + name, "success")
    elif action == "system":
        name = request.form['name']
        system = get_system(name)
        if system is None:
            flash("Invalid system name " + name, "danger")
            return redirect(url_for(".fleet"), code=303)

        if group.groupName == "default":
            groups = db.session.query(WaitlistGroup).all()
            for group in groups:
                group.system = system

            logger.info("All Systems were set to %s by %s", name, current_user.username, group.groupName)
            flash("All Systems were set to " + name, "success")
        else:
            group.system = system
            logger.info(group.displayName + " System was set to %s by %s", name, current_user.username)
            flash(group.displayName + " System was set to " + name, "success")
    elif action == "dock":
        name = request.form['name']
        station = get_station(name)
        if station is None:
            flash("Invalid station name " + name, "danger")
            return redirect(url_for(".fleet"), code=303)
        if group.displayName == "default":
            groups = db.session.query(WaitlistGroup).all()
            station = get_station(name)
            for group in groups:
                group.dockup = station

            logger.info("All Docks were set to %s by %s", name, current_user.username)
            flash("All Dock were set to " + name, "success")
        else:
            group.dockup = get_station(name)
            logger.info("%s Dock was set to %s by %s", group.displayName, name, current_user.username)
            flash(group.displayName + " Dock was set to " + name, "success")

    db.session.commit()

    return redirect(url_for(".fleet"), code=303)


@bp.route("/fleet/query/constellations", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_constellations():
    term = request.args['term']
    constellations = db.session.query(Constellation).filter(Constellation.constellationName.like(term + "%")).all()
    const_list = []
    for const in constellations:
        const_list.append({'conID': const.constellationID, 'conName': const.constellationName})
    return jsonify(result=const_list)


@bp.route("/fleet/query/systems", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_systems():
    term = request.args['term']
    systems = db.session.query(SolarSystem).filter(SolarSystem.solarSystemName.like(term + "%")).all()
    system_list = []
    for item in systems:
        system_list.append({'sysID': item.solarSystemID, 'sysName': item.solarSystemName})
    return jsonify(result=system_list)


@bp.route("/fleet/query/stations", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_stations():
    term = request.args['term']
    stations = db.session.query(Station).filter(Station.stationName.like(term + "%")).all()
    station_list = []
    for item in stations:
        station_list.append({'statID': item.station_id, 'statName': item.stationName})
    return jsonify(result=station_list)


@bp.route("/fleet/clear/<int:gid>", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def clear_waitlist(gid):
    group = db.session.query(WaitlistGroup).get(gid)
    logger.info("%s cleared waitlist %s", current_user.username, group.displayName)
    if group.otherlist is None:
        db.session.query(WaitlistEntry).filter(
            (WaitlistEntry.waitlist_id == group.xupwlID)
            | (WaitlistEntry.waitlist_id == group.logiwlID)
            | (WaitlistEntry.waitlist_id == group.dpswlID)
            | (WaitlistEntry.waitlist_id == group.sniperwlID)
        ).delete()
    else:
        db.session.query(WaitlistEntry).filter(
            (WaitlistEntry.waitlist_id == group.xupwlID)
            | (WaitlistEntry.waitlist_id == group.logiwlID)
            | (WaitlistEntry.waitlist_id == group.dpswlID)
            | (WaitlistEntry.waitlist_id == group.sniperwlID)
            | (WaitlistEntry.waitlist_id == group.otherwlID)
        ).delete()

    db.session.commit()
    flash("Waitlists were cleared!", "danger")
    return redirect(url_for('.fleet'))


@bp.route("/fleet/status/set/", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def fleet_status_global_set() -> str:
    action = request.form['action']
    if action == "set_name_scramble":
        should_scrable = not (request.form.get('scramble', 'off') == 'off')
        config.scramble_names = should_scrable
    return "OK"

add_menu_entry('fleetoptions.fleet', 'Fleet Settings', perm_management.can)
