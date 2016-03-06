from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.data.perm import perm_admin, perm_settings, perm_officer
from flask.templating import render_template
from flask.globals import request
from sqlalchemy import or_
from waitlist.storage.database import Account, Role, Character, roles,\
    linked_chars, CoporationBans, CorporationBans, AllianceBans
import flask
from waitlist.data.eve_xml_api import get_character_id_from_name
from werkzeug.utils import redirect
from flask.helpers import url_for
from waitlist.utility.utils import get_random_token, get_character_by_name
from waitlist import db

bp_settings = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

@bp_settings.route("/")
@login_required
@perm_settings.require(http_exception=401)
def overview():
    return render_template('settings/overview.html')

@bp_settings.route("/accounts", methods=["GET", "POST"])
@login_required
@perm_admin.require(http_exception=401)
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
@perm_settings.require(http_exception=401)
def fleet():
    return render_template("settings/fleet.html")


@bp_settings.route("/account_edit", methods=["POST"])
@login_required
@perm_admin.require(http_exception=401)
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
    banned_chars = db.session.query(Character).filter(Character.banned == True).all()
    banned_corps = db.session.query(CorporationBans).all()
    banned_alliances = db.session.query(AllianceBans).all()
    return render_template("settings/bans.html", banned_chars=banned_chars, corps=banned_corps, allis=banned_alliances)

@bp_settings.route("/bans_change", methods=["POST"])
@login_required
@perm_officer.require(http_exception=401)
def bans_change():
    action = request.form['change'] # ban, unban
    target_type = request.form['target_type'] # char,corp,alliance
    target = request.form['target'] # name of target
    reason = request.form['reason'] # reason for ban
    print 'action='+str(action)+" target="+str(target)
    if action is None or target is None or type is None:
        
        return flask.abort(400)
    
    if target_type == "char":
        char = get_character_by_name(target)
        
        if action == "ban":
            char.banned = True
            char.reason = reason
            # we need to log the user out
    
        elif action == "unban":
            char.banned = False
            char.reason = ""
        
        db.session.commit()
    if target_type == "corp":
        if action == "unban":
            db.session.query(CorporationBans).filter(CorporationBans.name == target).delete()
        if action == "ban":
            # check if ban already there
            if db.session.query(CorporationBans).filter(CorporationBans.name == target).count() <= 0:
                target_id = get_character_id_from_name(target)
                ban = CorporationBans()
                ban.id = target_id
                ban.name = target
                ban.reason = reason
                db.session.add(ban)
        db.session.commit()
        
    if target_type == "alliance":
        if action == "unban":
            db.session.query(AllianceBans).filter(AllianceBans.name == target).delete()
        if action == "ban":
            # check if ban already there
            if db.session.query(AllianceBans).filter(AllianceBans.name == target).count() <= 0:
                target_id = get_character_id_from_name(target)
                ban = AllianceBans()
                ban.id = target_id
                ban.name = target
                ban.reason = reason
                db.session.add(ban)
        db.session.commit()
    
    return redirect(url_for(".bans", code=303))

@bp_settings.route("/api/account/<int:acc_id>", methods=["DELETE"])
@login_required
@perm_admin.require(http_exception=401)
def api_account_delete(acc_id):
    db.session.query(Account).filter(Account.id == acc_id).delete();
    db.session.commit();
    return flask.jsonify(status="OK")

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