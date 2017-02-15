from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from gevent import Greenlet

from waitlist.data.perm import perm_admin, perm_settings, perm_officer, \
    perm_management, perm_accounts, perm_dev, perm_leadership, \
    perm_fleetlocation, perm_bans
from flask.templating import render_template
from flask.globals import request
from sqlalchemy import or_, asc
from waitlist.storage.database import Account, Role, Character, \
    linked_chars, Ban, Constellation, IncursionLayout, SolarSystem, Station, \
    WaitlistEntry, WaitlistGroup, Whitelist, TeamspeakDatum
import flask
from waitlist.data.eve_xml_api import get_character_id_from_name, get_char_info_for_character
from werkzeug.utils import redirect, secure_filename
from flask.helpers import url_for, flash
from waitlist.utility.utils import get_random_token, get_info_from_ban
from waitlist import db, app
from waitlist.utility.eve_id_utils import get_constellation, get_system, \
    get_station, get_character_by_name
from os import path
import os
from bz2 import BZ2File
from waitlist.utility import sde
from flask import jsonify
import csv
from waitlist.data.names import WTMRoles
from waitlist.utility.settings import settings
from waitlist.utility.settings.settings import sget_active_ts_id, \
    sset_active_ts_id, sget_resident_mail, sget_tbadge_mail, sget_resident_topic, \
    sget_tbadge_topic, sget_other_mail, sget_other_topic
from waitlist.ts3.connection import change_connection
from datetime import datetime, timedelta
from waitlist.data.sse import StatusChangedSSE, send_server_sent_event
from waitlist.utility import config
from waitlist.signal.signals import send_roles_changed, send_account_created, send_account_status_change
from waitlist.permissions import perm_manager
from flask.wrappers import Response
from sqlalchemy.orm import joinedload

bp_settings = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

@bp_settings.route("/fleet/query/constellations", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_constellations():
    term = request.args['term']
    constellations = db.session.query(Constellation).filter(Constellation.constellationName.like(term + "%")).all()
    const_list = []
    for const in constellations:
        const_list.append({'conID': const.constellationID, 'conName': const.constellationName})
    return jsonify(result=const_list)


@bp_settings.route("/fleet/query/systems", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_systems():
    term = request.args['term']
    systems = db.session.query(SolarSystem).filter(SolarSystem.solarSystemName.like(term + "%")).all()
    system_list = []
    for item in systems:
        system_list.append({'sysID': item.solarSystemID, 'sysName': item.solarSystemName})
    return jsonify(result=system_list)


@bp_settings.route("/fleet/query/stations", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_stations():
    term = request.args['term']
    stations = db.session.query(Station).filter(Station.stationName.like(term + "%")).all()
    station_list = []
    for item in stations:
        station_list.append({'statID': item.station_id, 'statName': item.stationName})
    return jsonify(result=station_list)


@bp_settings.route("/fleet/clear/<int:gid>", methods=["POST"])
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


@bp_settings.route("/accounts/import/accounts", methods=["POST"])
@login_required
@perm_leadership.require(http_exception=401)
def accounts_import_accounts():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "csv"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if path.isfile(dest_name):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        update_accounts_by_file(dest_name)
        flash("Accounts were updated!", "success")

    return redirect(url_for('.accounts'))


def update_accounts_by_file(filename):
    key_name = "FC Chat Pull"
    key_main = "Main's Name"
    key_roles = "Current Status"
    if not path.isfile(filename):
        return

    if filename.rsplit('.', 1)[1] == "csv":
        f = open(filename, 'r')
    elif filename.rsplit('.', 1)[1] == "bz2":
        f = BZ2File(filename)
    else:
        return

    reader = csv.DictReader(f, delimiter="\t", quotechar='\\')

    # batch cache all chars beforehand so we don't hit api limits
    chars_to_cache = []
    char_dict = {}
    main_dict = {}
    for row in reader:
        pull_name = row[key_name].strip()
        main_name = row[key_main].strip()
        sheet_roles = row[key_roles].strip().split(",")
        wl_roles = [convert_role_names(x.strip()) for x in sheet_roles]
        if pull_name not in char_dict:
            char_dict[pull_name] = None
        if main_name not in char_dict:
            char_dict[main_name] = None

        if main_name not in main_dict:
            main_dict[main_name] = {'main': None, 'alts': [], 'roles': wl_roles}
        else:
            main = main_dict[main_name]
            for wl_role in wl_roles:
                if wl_role not in main['roles']:
                    if wl_role == WTMRoles.tbadge and WTMRoles.fc in main['roles']:
                        continue
                    if wl_role == WTMRoles.resident and WTMRoles.lm in main['roles']:
                        continue
                    main['roles'].append(wl_role)

        if main_name == pull_name:
            main_dict[main_name]['main'] = pull_name
        else:
            main_dict[main_name]['alts'].append(pull_name)

    for char_name in char_dict:
        chars_to_cache.append(char_name)

    for main_name in main_dict:
        acc = db.session.query(Account).filter(Account.username == main_name).first()
        if acc is not None:
            continue

        acc_pw = None
        acc_email = None
        main = main_dict[main_name]
        acc_roles = main['roles']

        main_char = get_character_by_name(main['main'])
        if main_char is None:
            flash("Failed to get Character for Name " + main['main'], "danger")
            continue

        acc = Account()
        acc.username = main_name
        if acc_pw is not None:
            acc.set_password(acc_pw.encode('utf-8'))
        acc.login_token = get_random_token(16)
        acc.email = acc_email
        if len(acc_roles) > 0:
            db_roles = db.session.query(Role).filter(or_(Role.name == name for name in acc_roles)).all()
            for role in db_roles:
                acc.roles.append(role)

        db.session.add(acc)

        acc.characters.append(main_char)

        for alt in main['alts']:
            # find out if there is a character like that in the database
            character = get_character_by_name(alt)
            if character is None:
                flash("Failed to get character for alt with name " + alt, "danger")
            else:
                acc.characters.append(character)

                db.session.flush()

        acc.current_char = main_char.get_eve_id()

    db.session.commit()
    f.close()


def convert_role_names(sheet_name):
    convert_obj = {'FC': WTMRoles.fc, 'RES': WTMRoles.resident,
                   'LM': WTMRoles.lm, 'TRA': WTMRoles.tbadge}
    return convert_obj[sheet_name]


@bp_settings.route("/whitelist", methods=["GET"])
@login_required
@perm_bans.require(http_exception=401)
def whitelist():
    whitelistings = db.session.query(Whitelist).join(Character, (Whitelist.characterID == Character.id)).order_by(
        asc(Character.eve_name)).all()
    return render_template("settings/whitelist.html", wl=whitelistings)


@bp_settings.route("/whitelist_change", methods=["POST"])
@login_required
@perm_leadership.require(http_exception=401)
def whitelist_change():
    action: str = request.form['change']  # whitelist, unwhitelist
    target: str = request.form['target']  # name of target
    reason = ''
    if action == "whitelist":
        reason: str = request.form['reason']  # reason for whitelist

    targets = target.split("\n")

    # pre-cache names for a faster api to not hit request limit
    names_to_cache = []
    for line in targets:
        line = line.strip()
        wl_name, _, wl_admin = get_info_from_ban(line)
        names_to_cache.append(wl_name)
        if wl_admin is not None:
            names_to_cache.append(wl_admin)

    if action == "whitelist":
        for target in targets:
            whitelist_by_name(target, True, reason)

    elif action == "unwhitelist":
        for target in targets:
            unwhitelist_by_name(target)

    return redirect(url_for(".whitelist"))


'''
@param ban_info: a eve character name, or copy from ingame chat window
'''


def whitelist_by_name(whitelist_info, leadership=False, reason=""):
    target = whitelist_info.strip()

    wl_name, wl_reason, wl_admin = get_info_from_ban(target)

    if wl_reason is None or not leadership:
        wl_reason = reason

    if wl_admin is None or not leadership:
        wl_admin = current_user.get_eve_name()

    logger.info("Whitelisting %s for %s by %s as %s.", wl_name, wl_reason, wl_admin, current_user.username)
    wl_char = get_character_by_name(wl_name)
    admin_char = get_character_by_name(wl_admin)
    if wl_char is None:
        logger.error("Did not find whitelist target %s", wl_name)
        flash("Could not find Character " + wl_name + " for whitelisting", "danger")
        return

    eve_id = wl_char.get_eve_id()
    admin_id = admin_char.get_eve_id()

    if eve_id is None or admin_id is None:
        logger.error("Failed to correctly parse: %", target)
        flash("Failed to correctly parse " + target, "danger")
        return

    # check if ban already there
    if db.session.query(Whitelist).filter(Whitelist.characterID == eve_id).count() == 0:
        # ban him
        new_whitelist = Whitelist()
        new_whitelist.character = wl_char
        new_whitelist.reason = wl_reason
        new_whitelist.admin = admin_char
        db.session.add(new_whitelist)
        db.session.commit()


def unwhitelist_by_name(char_name):
    target = char_name.strip()
    logger.info("%s is unwhitelisting %s", current_user.username, target)
    eve_id = get_character_id_from_name(target)
    if eve_id == 0:
        flash("Character " + target + " does not exist!")
    else:
        # check that there is a ban
        if db.session.query(Whitelist).filter(Whitelist.characterID == eve_id).count() > 0:
            db.session.query(Whitelist).filter(Whitelist.characterID == eve_id).delete()
            db.session.commit()


@bp_settings.route("/whitelist_change_single", methods=["POST"])
@login_required
@perm_bans.require(http_exception=401)
def whitelist_change_single():
    action = request.form['change']  # whitelist, unwhitelist
    target = request.form['target']  # name of target

    target = target.strip()

    if action == "whitelist":
        reason = request.form['reason']  # reason for ban
        whitelist_by_name(target, perm_leadership.can(), reason)
    elif action == "unwhitelist":
        unwhitelist_by_name(target)

    return redirect(url_for(".withelist"))


@bp_settings.route("/whitelist_unlist", methods=["POST"])
@login_required
@perm_bans.require(http_exception=401)
def whitelist_unlist():
    target = request.form['target']  # name of target
    target = target.strip()
    unwhitelist_by_name(target)

    return redirect(url_for(".whitelist"))


@bp_settings.route("/ts", methods=["GET"])
@login_required
@perm_management.require()
def teamspeak():
    active_ts_setting_id = settings.sget_active_ts_id()
    active_ts_setting = None
    if active_ts_setting_id is not None:
        active_ts_setting = db.session.query(TeamspeakDatum).get(active_ts_setting_id)

    all_ts_settings = db.session.query(TeamspeakDatum).all()

    return render_template("settings/ts.html", active=active_ts_setting, all=all_ts_settings)


@bp_settings.route("/ts", methods=["POST"])
@login_required
@perm_management.require()
def teamspeak_change():
    action = request.form['action']  # add/remove, set
    if action == "add" and perm_leadership.can():
        display_name = request.form['displayName']
        host = request.form['internalHost']
        port = int(request.form['internalPort'])
        display_host = request.form['displayHost']
        display_port = int(request.form['displayPort'])
        query_name = request.form['queryName']
        query_password = request.form['queryPassword']
        server_id = int(request.form['serverID'])
        channel_id = int(request.form['channelID'])
        client_name = request.form['clientName']
        safety_channel_id = request.form['safetyChannelID']
        ts = TeamspeakDatum(
            displayName=display_name,
            host=host,
            port=port,
            displayHost=display_host,
            displayPort=display_port,
            queryName=query_name,
            queryPassword=query_password,
            serverID=server_id,
            channelID=channel_id,
            clientName=client_name,
            safetyChannelID=safety_channel_id
        )
        db.session.add(ts)
        db.session.commit()
    elif action == "remove" and perm_leadership.can():
        teamspeak_id = int(request.form['teamspeakID'])
        db.session.query(TeamspeakDatum).filter(TeamspeakDatum.teamspeakID == teamspeak_id).delete()
        active_id = sget_active_ts_id()
        if active_id is not None and active_id == teamspeak_id:
            sset_active_ts_id(None)
            change_connection()
        db.session.commit()
    elif action == "set":
        teamspeak_id = int(request.form['teamspeakID'])
        active_id = sget_active_ts_id()
        sset_active_ts_id(teamspeak_id)
        if active_id is None or active_id != teamspeak_id:
            change_connection()
    else:
        flask.abort(400)

    return redirect(url_for("settings.teamspeak"))


@bp_settings.route("/fleet/status/set/", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def fleet_status_global_set():
    action = request.form['action']
    if action == "set_name_scramble":
        should_scrable = not (request.form.get('scramble', 'off') == 'off')
        config.scramble_names = should_scrable
    return "OK"


@bp_settings.route('/accounts/downloadlist/cvs')
@login_required
@perm_manager.require('leadership')
def accounts_download_csv():
    def iter_accs(data):
        for account in data:
            for ci, char in enumerate(account.characters):
                if ci > 0:
                    yield ", " + char.eve_name
                else:
                    yield char.eve_name
            yield '\n'

    accs = db.session.query(Account).options(joinedload('characters')).join(Account.roles).filter(
        ((Role.name == WTMRoles.fc) | (Role.name == WTMRoles.lm)) & (Account.disabled is False)).order_by(
        Account.username).all()

    response = Response(iter_accs(accs), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=accounts.csv'
    return response


'''
@bp_settings.route("/api/account/", methods=["POST"])
@login_required
@perm_admin.require(http_exception=401)
def api_account_create():
'''

'''
@bp_settings.route("/create_account", methods=['GET'])
@perm_admin.require(http_exception=401)
def create_account_form():
    roles = WTMRoles.get_role_list()
    return render_template("create_account_form.html", roles=roles)
'''
