from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.data.perm import perm_admin, perm_settings, perm_officer,\
    perm_management, perm_accounts, perm_dev
from flask.templating import render_template
from flask.globals import request
from sqlalchemy import or_
from waitlist.storage.database import Account, Role, Character, roles,\
    linked_chars, Ban, Constellation, IncursionLayout
import flask
from waitlist.data.eve_xml_api import get_character_id_from_name
from werkzeug.utils import redirect, secure_filename
from flask.helpers import url_for, flash
from waitlist.utility.utils import get_random_token
from waitlist import db, app
from waitlist.utility.eve_id_utils import get_constellation, get_system,\
    get_station
from os import path
import os
from bz2 import BZ2File
from waitlist.blueprints.fleetstatus import fleet_status
from waitlist.utility import sde
from flask import jsonify

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
    
        acc = Account()
        acc.username = acc_name
        if acc_pw is not None:
            acc.set_password(acc_pw.encode('utf-8'))
        acc.login_token = get_random_token(64)
        acc.email = acc_email
        if len(acc_roles) > 0:
            db_roles = db.session.query(Role).filter(or_(Role.name == name for name in acc_roles)).all()
            for role in db_roles:
                acc.roles.append(role)
    
        db.session.add(acc)

        char_id = get_character_id_from_name(char_name)
    
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
    return render_template("settings/fleet.html", fleet=fleet_status)


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
                print roles_new
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
@perm_officer.require(http_exception=401)
def bans():
    bans = db.session.query(Ban).all()
    return render_template("settings/bans.html", bans=bans)

@bp_settings.route("/bans_change", methods=["POST"])
@login_required
@perm_officer.require(http_exception=401)
def bans_change():
    action = request.form['change'] # ban, unban
    target = request.form['target'] # name of target
    if action == "ban":
        reason = request.form['reason'] # reason for ban
    
    targets = target.split("\n")
    
    
    
    if action == "ban":
        for target in targets:
            target = target.strip()
            logger.info("Banning >%s<", target)
            eve_id = get_character_id_from_name(target)
            #check if ban already there
            if db.session.query(Ban).filter(Ban.id == eve_id).count() == 0:
                # ban him
                new_ban = Ban()
                new_ban.id = eve_id
                new_ban.name = target
                new_ban.reason = reason
                db.session.add(new_ban)
                db.session.commit()
    elif action == "unban":
        for target in targets:
            target = target.strip()
            logger.info("Unbanning >%s<", target)
            eve_id = get_character_id_from_name(target)
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
        fleet_status.status = text
        flash("Status was set to "+text, "success")
    elif action == "fc":
        name = request.form['name']
        eve_id = get_character_id_from_name(name)
        fleet_status.fc = [name, eve_id]
        flash("FC was set to "+name, "success")
    elif action == "manager":
        name = request.form['name']
        eve_id = get_character_id_from_name(name)
        fleet_status.manager = [name, eve_id]
        flash("Manager was set to "+name, "success")
    elif action == "constellation":
        name = request.form['name']
        const_id = get_constellation(name).constellationID
        fleet_status.constellation = [name, const_id]
        # if we set the constellation look up if we already know dock and hq system
        inc_layout = db.session.query(IncursionLayout).filter(IncursionLayout.constellation == const_id).first()
        # if we know it, set the other information
        if inc_layout is not None:
            fleet_status.systemhq = [inc_layout.obj_headquarter.solarSystemName, inc_layout.obj_headquarter.solarSystemID]
            fleet_status.dock = [inc_layout.obj_dockup.stationName, inc_layout.obj_dockup.stationID]            
        flash("Constellation was set to "+name, "success")
    elif action == "systemhq":
        name = request.form['name']
        system_id = get_system(name).solarSystemID
        fleet_status.systemhq = [name, system_id]
        flash("HQ System was set to "+name, "success")
    elif action == "dock":
        name = request.form['name']
        station_id = get_station(name).stationID
        fleet_status.dock = [name, station_id]
        flash("Dock was set to "+name, "success")
    
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
    constellations = db.session.query(Constellation).filter(Constellation.constellationName.like("%"+term+"%")).all()
    const_list = []
    for const in constellations:
        const_list.append({'conID': const.constellationID, 'conName': const.constellationName})
    return jsonify(result=const_list)


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