from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from waitlist.data.perm import WTMRoles, perm_admin, perm_settings,\
    perm_management
from flask.templating import render_template
from flask.globals import request
from waitlist.utils import get_random_token
import evelink
from sqlalchemy import or_
from waitlist.storage.database import Account, Role, session, Character

bp_settings = Blueprint('settings', __name__, template_folder='templates')
logger = logging.getLogger(__name__)

@bp_settings.route("/")
@login_required
@perm_settings.require(http_exception=401)
def settings():
    return render_template('settings.html', perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management)

@bp_settings.route("/accounts")
@login_required
@perm_admin.require(http_exception=401)
def accounts():
    return render_template("accounts.html", perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management)

@bp_settings.route('/fmangement')
@login_required
@perm_settings.require(http_exception=401)
def management():
    return render_template("fleet_management.html", perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management)

@bp_settings.route("/create_account", methods=['GET'])
@perm_admin.require(http_exception=401)
def create_account_form():
    roles = WTMRoles.get_role_list()
    return render_template("create_account_form.html", roles=roles, perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management)

@bp_settings.route('/create_account', methods=["POST"])
@perm_admin.require(http_exception=401)
def create_account():
    name = request.form['account_name']
    pw = request.form['account_pw']
    roles = request.form.getlist('account_roles')
    email = request.form['account_email']
    char_name = request.form['default_char_name']
    char_name = char_name.strip()

    acc = Account()
    acc.username = name
    acc.set_password(pw)
    acc.login_token = get_random_token(64)
    acc.email = email
    roles = session.query(Role).filter(or_(Role.name == name for name in roles)).all()
    for role in roles:
        acc.roles.append(role)

    session.add(acc)
    
    eve = evelink.eve.EVE()
        
    response = eve.character_id_from_name(char_name)
    char_id = int(response.result)

    character = Character()
    character.eve_name = char_name
    character.id = char_id
    acc.characters.append(character)
    
    session.commit()

    acc.current_char = char_id
    
    session.commit()

    roles = WTMRoles.get_role_list()
    return render_template("create_account_form.html", roles=roles, perm_admin=perm_admin, perm_settings=perm_settings, perm_man=perm_management)
    