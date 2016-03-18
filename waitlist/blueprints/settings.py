from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.data.perm import perm_admin, perm_settings, perm_officer,\
    perm_management, perm_accounts, perm_dev, perm_leadership,\
    perm_fleetlocation, perm_bans
from flask.templating import render_template
from flask.globals import request
from sqlalchemy import or_, desc
from waitlist.storage.database import Account, Role, Character, roles,\
    linked_chars, Ban, Constellation, IncursionLayout, SolarSystem, Station,\
    WaitlistEntry
import flask
from waitlist.data.eve_xml_api import get_character_id_from_name,\
    eve_api_cache_char_ids
from werkzeug.utils import redirect, secure_filename
from flask.helpers import url_for, flash
from waitlist.utility.utils import get_random_token, get_info_from_ban,\
    get_character_by_name
from waitlist import db, app
from waitlist.utility.eve_id_utils import get_constellation, get_system,\
    get_station
from os import path
import os
from bz2 import BZ2File
from waitlist.blueprints.fleetstatus import fleet_status
from waitlist.utility import sde
from flask import jsonify
import csv
from waitlist.data.names import WTMRoles

bp_settings = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

@bp_settings.route("/")
@login_required
@perm_settings.require(http_exception=401)
def overview():
    return render_template('settings/overview.html')

@bp_settings.route("/accounts", methods=["GET", "POST"])
@login_required
@perm_accounts.require(http_exception=401)
def accounts():
    if request.method == "POST":
        acc_name = request.form['account_name']
        acc_pw = request.form['account_pw']
        if acc_pw == "":
            acc_pw = None

        acc_roles = request.form.getlist('account_roles')
        acc_email = request.form['account_email']
        if acc_email == "":
            acc_email = None

        char_name = request.form['default_char_name']
        char_name = char_name.strip()
        
        char_id = get_character_id_from_name(char_name)
        if char_id == 0:
            flash("This Character does not exist!")
        else:
            acc = Account()
            acc.username = acc_name
            if acc_pw is not None:
                acc.set_password(acc_pw.encode('utf-8'))
            acc.login_token = get_random_token(16)
            acc.email = acc_email
            if len(acc_roles) > 0:
                db_roles = db.session.query(Role).filter(or_(Role.name == name for name in acc_roles)).all()
                for role in db_roles:
                    acc.roles.append(role)
        
            db.session.add(acc)
        
            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()
            
            if character is None:
                character = Character()
                character.eve_name = char_name
                character.id = char_id
    
            acc.characters.append(character)
            
            db.session.flush()
        
            acc.current_char = char_id
            
            db.session.commit()
    

    roles = db.session.query(Role).order_by(Role.name).all();
    accounts = db.session.query(Account).order_by(Account.username).all()
    
    return render_template("settings/accounts.html", roles=roles, accounts=accounts)

@bp_settings.route('/fmangement')
@login_required
@perm_management.require(http_exception=401)
def fleet():
    return render_template("settings/fleet.html", fleet=fleet_status, user=current_user)


@bp_settings.route("/account_edit", methods=["POST"])
@login_required
@perm_accounts.require(http_exception=401)
def account_edit():
    acc_id = int(request.form['account_id'])
    acc_name = request.form['account_name']
    acc_pw = request.form['account_pw']
    if acc_pw == "":
        acc_pw = None

    acc_roles = request.form.getlist('account_roles')
    acc_email = request.form['account_email']
    if acc_email == "":
        acc_email = None

    char_name = request.form['default_char_name']
    char_name = char_name.strip()
    if char_name == "":
        char_name = None

    acc = db.session.query(Account).filter(Account.id == acc_id).first();
    if acc == None:
        return flask.abort(400)
    
    if (acc.username != acc_name):
        acc.username = acc_name
    if acc_pw is not None:
        acc.set_password(acc_pw.encode('utf-8'))
    #acc.login_token = get_random_token(64)
    if acc_email is not None:
        acc.email = acc_email
    if len(acc_roles) > 0:
        roles_new = {}
        for r in acc_roles:
            roles_new[r] = True
        
        #db_roles = session.query(Role).filter(or_(Role.name == name for name in acc_roles)).all()
        roles_to_remove = []
        for role in acc.roles:
            if role.name in roles_new:
                del roles_new[role.name] # remove because it is already in the db
            else:
                # remove the roles because it not submitted anymore
                roles_to_remove.append(role) # mark for removal
        
        for role in roles_to_remove:
            acc.roles.remove(role)
        
        
        
        # add remaining roles
        if len(roles_new) >0 :
            new_roles = db.session.query(Role).filter(or_(Role.name == name for name in roles_new))
            for role in new_roles:
                acc.roles.append(role)
    else:
        # make sure all roles are removed#
        db.session.query(roles).filter(roles.c.account_id == acc_id).delete()
        db.session.flush()

    if char_name is not None:
        char_id = get_character_id_from_name(char_name)
        if char_id == 0:
            flash("Character "+char_name+" does not exist!")
        else:
            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()
        
            if character is None:
                character = Character()
                character.eve_name = char_name
                character.id = char_id
    
            # check if character is linked to this account
            link = db.session.query(linked_chars).filter((linked_chars.c.id == acc_id) & (linked_chars.c.char_id == char_id)).first();
            if link is None:
                acc.characters.append(character)
            
            db.session.flush()
            acc.current_char = char_id
    
    db.session.commit()
    return redirect(url_for('.accounts'), code=303)

@bp_settings.route("/account_self_edit", methods=["POST"])
@login_required
@perm_settings.require(http_exception=401)
def account_self_edit():
    acc_id = current_user.id
    acc_pw = request.form['account_pw']
    if acc_pw == "":
        acc_pw = None

    acc_email = request.form['account_email']
    if acc_email == "":
        acc_email = None

    char_name = request.form['default_char_name']
    char_name = char_name.strip()
    if char_name == "":
        char_name = None

    acc = db.session.query(Account).filter(Account.id == acc_id).first();
    if acc == None:
        return flask.abort(400)

    if acc_pw is not None:
        acc.set_password(acc_pw.encode('utf-8'))
    #acc.login_token = get_random_token(64)
    if acc_email is not None:
        acc.email = acc_email

    if char_name is not None:
        char_id = get_character_id_from_name(char_name)
        
        if char_id == 0:
            flash("Character " + char_name + " does not exist!")
        else:
            
            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()
        
            if character is None:
                character = Character()
                character.eve_name = char_name
                character.id = char_id
        
            # check if character is linked to this account
            link = db.session.query(linked_chars).filter((linked_chars.c.id == acc_id) & (linked_chars.c.char_id == char_id)).first();
            if link is None:
                acc.characters.append(character)
            
            db.session.flush()
            acc.current_char = char_id
    
    db.session.commit()
    return redirect(url_for('.account_self'), code=303)

@bp_settings.route("/account_self", methods=["GET"])
@login_required
@perm_settings.require(http_exception=401)
def account_self():
    acc = db.session.query(Account).filter(Account.id == current_user.id).first()
    return render_template("settings/self.html", account=acc)

@bp_settings.route("/bans", methods=["GET"])
@login_required
@perm_bans.require(http_exception=401)
def bans():
    bans = db.session.query(Ban).order_by(desc(Ban.name)).all()
    return render_template("settings/bans.html", bans=bans)

@bp_settings.route("/bans_change", methods=["POST"])
@login_required
@perm_leadership.require(http_exception=401)
def bans_change():
    action = request.form['change'] # ban, unban
    target = request.form['target'] # name of target
    if action == "ban":
        reason = request.form['reason'] # reason for ban
    
    targets = target.split("\n")

    # pre-cache names for a faster api to not hit request limit
    names_to_cache = []
    for line in targets:
        line = line.strip()
        ban_name, _, ban_admin = get_info_from_ban(line)
        names_to_cache.append(ban_name)
        if ban_admin is not None:
            names_to_cache.append(ban_admin)
    
    eve_api_cache_char_ids(names_to_cache)
    
    if action == "ban":
        for target in targets:
            target = target.strip()
            
            ban_name, ban_reason, ban_admin = get_info_from_ban(target)
            
            if ban_reason == None:
                ban_reason = reason
            
            if ban_admin is None:
                ban_admin = current_user.get_eve_name()
            
            logger.info("Banning %s for %s by %s as %s.", ban_name, ban_reason, ban_admin, current_user.username)
            ban_char = get_character_by_name(ban_name)
            admin_char = get_character_by_name(ban_admin)
            if ban_char is None:
                logger.error("Did not find ban target %s", ban_name)
                flash("Could not find Character " + ban_name, "danger")
                continue

            eve_id = ban_char.get_eve_id()
            admin_id = admin_char.get_eve_id()
            
            if eve_id is None or admin_id is None:
                logger.error("Failed to correctly parse: %", target)
                flash("Failed to correctly parse " + target, "danger")
                continue

            #check if ban already there
            if db.session.query(Ban).filter(Ban.id == eve_id).count() == 0:
                # ban him
                new_ban = Ban()
                new_ban.id = eve_id
                new_ban.name = ban_name
                new_ban.reason = ban_reason
                new_ban.admin = admin_id
                db.session.add(new_ban)
                db.session.commit()
    elif action == "unban":
        for target in targets:
            target = target.strip()
            logger.info("%s is unbanning %s", current_user.username, target)
            eve_id = get_character_id_from_name(target)
            if eve_id == 0:
                flash("Character " + target + " does not exist!")
            else:
                # check that there is a ban
                if db.session.query(Ban).filter(Ban.id == eve_id).count() > 0:
                    db.session.query(Ban).filter(Ban.id == eve_id).delete()
                    db.session.commit()
    
    return redirect(url_for(".bans", code=303))

@bp_settings.route("/bans_change_single", methods=["POST"])
@login_required
@perm_bans.require(http_exception=401)
def bans_change_single():
    action = request.form['change'] # ban, unban
    target = request.form['target'] # name of target

    target = target.strip()
    
    ban_admin = current_user.get_eve_name()
    ban_name = target

    
    
    if action == "ban":
        reason = request.form['reason'] # reason for ban
        ban_char = get_character_by_name(ban_name)
        admin_char = get_character_by_name(ban_admin)
        logger.info("Banning %s for %s as %s.", ban_name, reason, current_user.username)
        if ban_char is None:
            logger.error("Did not find ban target %s", ban_name)
            flash("Could not find Character " + ban_name, "danger")
            return

        eve_id = ban_char.get_eve_id()
        admin_id = admin_char.get_eve_id()
        
        if eve_id is None or admin_id is None:
            logger.error("Failed to correctly parse: %", target)
            flash("Failed to correctly parse " + target, "danger")
            return

        #check if ban already there
        if db.session.query(Ban).filter(Ban.id == eve_id).count() == 0:
            # ban him
            new_ban = Ban()
            new_ban.id = eve_id
            new_ban.name = ban_name
            new_ban.reason = reason
            new_ban.admin = admin_id
            db.session.add(new_ban)
            db.session.commit()
    elif action == "unban":
        logger.info("%s is unbanning %s", current_user.username, target)
        eve_id = get_character_id_from_name(target)
        if eve_id == 0:
            flash("Character " + target + " does not exist!")
        else:
            # check that there is a ban
            if db.session.query(Ban).filter(Ban.id == eve_id).count() > 0:
                db.session.query(Ban).filter(Ban.id == eve_id).delete()
                db.session.commit()

    return redirect(url_for(".bans", code=303))

@bp_settings.route("/bans_unban", methods=["POST"])
@login_required
@perm_bans.require(http_exception=401)
def bans_unban_single():
    target = request.form['target'] # name of target
    target = target.strip()
    logger.info("%s is unbanning %s", current_user.username, target)
    eve_id = get_character_id_from_name(target)
    if eve_id == 0:
        flash("Character " + target + " does not exist!")
    else:
        # check that there is a ban
        if db.session.query(Ban).filter(Ban.id == eve_id).count() > 0:
            db.session.query(Ban).filter(Ban.id == eve_id).delete()
            db.session.commit()
    
    return redirect(url_for(".bans", code=303))

@bp_settings.route("/api/account/<int:acc_id>", methods=["DELETE"])
@login_required
@perm_admin.require(http_exception=401)
def api_account_delete(acc_id):
    db.session.query(Account).filter(Account.id == acc_id).delete();
    db.session.commit();
    return flask.jsonify(status="OK")

@bp_settings.route("/fleet/status/set", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def fleet_status_set():
    action = request.form['action']

    if action == "status":
        text = request.form['status']
        xup = request.form.get('xup', 'off')
        xup_text = "closed"
        if xup == 'off':
            xup = False
        else:
            xup = True
            xup_text = "open"

        if xup != fleet_status.xup_enabled:
            fleet_status.xup_enabled = xup
            logger.info("XUP was set to %s by %s", xup, current_user.username)

        if perm_leadership.can() and perm_officer.can():
            fleet_status.status = text
            logger.info("Status was set to %s by %s", fleet_status.status, current_user.username)
            flash("Status was set to "+text+", xup is "+xup_text, "success")
            
        else:
            if text == "Running" or text == "Down" or text == "Forming":
                fleet_status.status = text
                logger.info("Status was set to %s by %s", fleet_status.status, current_user.username)
                flash("Status was set to "+text+", xup is "+xup_text, "success")
            else:
                logger.info("%s tried to set the status to %s and did not have the rights", current_user.username, fleet_status.status)
                flash("You do not have the rights to change the status to "+text, "danger")
                flash("XUP is now "+xup_text, "success")
    elif action == "fc":
        name = request.form['name']
        eve_id = get_character_id_from_name(name)
        if eve_id == 0:
            flash("Character " + name + " does not exist!")
        else:
            fleet_status.fc = [name, eve_id]
            flash("FC was set to "+name, "success")
    elif action == "manager":
        name = request.form['name']
        eve_id = get_character_id_from_name(name)
        if eve_id == 0:
            flash("Character " + name + " does not exist!")
        else:
            fleet_status.manager = [name, eve_id]
            flash("Manager was set to "+name, "success")
    
    return redirect(url_for(".fleet"), code=303)

@bp_settings.route("/fleet/location/set", methods=["POST"])
@login_required
@perm_fleetlocation.require(http_exception=401)
def fleet_location_set():
    action = request.form['action']
    if action == "constellation":
        name = request.form['name']
        const_id = get_constellation(name).constellationID
        fleet_status.constellation = [name, const_id]
        logger.info("Constellation was set to %s by %s", name, current_user.username)
        # if we set the constellation look up if we already know dock and hq system
        inc_layout = db.session.query(IncursionLayout).filter(IncursionLayout.constellation == const_id).first()
        # if we know it, set the other information
        if inc_layout is not None:
            fleet_status.systemhq = [inc_layout.obj_headquarter.solarSystemName, inc_layout.obj_headquarter.solarSystemID]
            logger.info("HQ System was autoset to %s by %s", fleet_status.systemhq[0], current_user.username)
            fleet_status.dock = [inc_layout.obj_dockup.stationName, inc_layout.obj_dockup.stationID]   
            logger.info("Dock was autoset to %s by %s", fleet_status.dock[0], current_user.username)
                 
        flash("Constellation was set to " + name, "success")
    elif action == "systemhq":
        name = request.form['name']
        system_id = get_system(name).solarSystemID
        fleet_status.systemhq = [name, system_id]
        logger.info("HQ System was set to %s by %s", name, current_user.username)
        flash("HQ System was set to "+name, "success")
    elif action == "dock":
        name = request.form['name']
        station_id = get_station(name).stationID
        fleet_status.dock = [name, station_id]
        logger.info("Dock was set to %s by %s", name, current_user.username)
        flash("Dock was set to " + name, "success")

    return redirect(url_for(".fleet"), code=303)

@bp_settings.route("/sde/update/typeids", methods=["POST"])
@login_required
@perm_dev.require(http_exception=401)
def update_type_ids():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "yaml"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if (path.isfile(dest_name)):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        sde.update_invtypes(dest_name)
        flash("Type IDs where updated!", "success")
    
    return redirect(url_for('.sde_settings'))

@bp_settings.route("/sde/update/map", methods=["POST"])
@login_required
@perm_dev.require(http_exception=401)
def update_map():
    f = request.files['file']
    file_ext = f.filename.rsplit('.', 1)[1]
    if f and (file_ext == "bz2" or file_ext == "db"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if (path.isfile(dest_name)):
            os.remove(dest_name)
        f.save(dest_name)
        
        # if it is bz2 extract it
        if (file_ext == "bz2"):
            raw_file = dest_name.rsplit(".", 1)[0]
            with open(raw_file, 'wb') as new_file, BZ2File(dest_name, 'rb') as f:
                for data in iter(lambda : f.read(100 * 1024), b''):
                    new_file.write(data)
            
        # start the update
        sde.update_constellations(raw_file)
        sde.update_systems(raw_file)
        flash("Constellations and Systems where updated!", "success")
    
    return redirect(url_for('.sde_settings'))

@bp_settings.route("/sde/update/stations", methods=["POST"])
@login_required
@perm_dev.require(http_exception=401)
def update_stations():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "csv"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if (path.isfile(dest_name)):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        sde.update_stations(dest_name)
        flash("Stations where updated!", "success")
    
    return redirect(url_for('.sde_settings'))

@bp_settings.route("/sde/update/layouts", methods=["POST"])
@login_required
@perm_dev.require(http_exception=401)
def update_layouts():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "csv"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if (path.isfile(dest_name)):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        sde.update_layouts(dest_name)
        flash("Layouts where updated!", "success")
    
    return redirect(url_for('.sde_settings'))

@bp_settings.route("/sde")
@login_required
@perm_dev.require(http_exception=401)
def sde_settings():
    return render_template("settings/sde.html")

@bp_settings.route("/fleet/query/constellations", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_constellations():
    term = request.args['term']
    constellations = db.session.query(Constellation).filter(Constellation.constellationName.like(term+"%")).all()
    const_list = []
    for const in constellations:
        const_list.append({'conID': const.constellationID, 'conName': const.constellationName})
    return jsonify(result=const_list)

@bp_settings.route("/fleet/query/systems", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_systems():
    term = request.args['term']
    systems = db.session.query(SolarSystem).filter(SolarSystem.solarSystemName.like(term+"%")).all()
    system_list = []
    for item in systems:
        system_list.append({'sysID': item.solarSystemID, 'sysName': item.solarSystemName})
    return jsonify(result=system_list)

@bp_settings.route("/fleet/query/stations", methods=["GET"])
@login_required
@perm_management.require(http_exception=401)
def fleet_query_stations():
    term = request.args['term']
    stations = db.session.query(Station).filter(Station.stationName.like(term+"%")).all()
    station_list = []
    for item in stations:
        station_list.append({'statID': item.stationID, 'statName': item.stationName})
    return jsonify(result=station_list)

@bp_settings.route("/fleet/clear/", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def clear_waitlist():
    db.session.query(WaitlistEntry).delete()
    db.session.commit()
    flash("Waitlists where cleared!", "danger")
    return redirect(url_for('.fleet'))

@bp_settings.route("/accounts/import/accounts", methods=["POST"])
@login_required
@perm_officer.require(http_exception=401)
def accounts_import_accounts():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "csv"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if (path.isfile(dest_name)):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        update_accounts_by_file(dest_name)
        flash("Accounts where updated!", "success")
    
    return redirect(url_for('.accounts'))

def update_accounts_by_file(filename):
    key_name = "FC Chat Pull"
    key_main = "Main's Name"
    key_roles = "Current Status"
    if not path.isfile(filename):
        return

    if filename.rsplit('.', 1)[1] == "csv" :
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
        if not pull_name in char_dict:
            char_dict[pull_name] = None
        if not main_name in char_dict:
            char_dict[main_name] = None

        if not main_name in main_dict:
            main_dict[main_name] = {'main': None, 'alts': [], 'roles': wl_roles}
        else:
            main = main_dict[main_name]
            for wl_role in wl_roles:
                if not wl_role in main['roles']:
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
    
    eve_api_cache_char_ids(chars_to_cache)
    
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
            flash("Failed to get Character for Name "+ main['main'], "danger")
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