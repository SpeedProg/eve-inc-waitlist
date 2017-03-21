import csv
import logging
import os
from bz2 import BZ2File
from typing import Union

import flask
from flask import Blueprint
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required, current_user
from os import path
from pyswagger.contrib.client import flask
from sqlalchemy import asc
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from waitlist import db, app
from waitlist.blueprints.settings import add_menu_entry
from waitlist.data.eve_xml_api import get_character_id_from_name, get_char_info_for_character
from waitlist.data.names import WTMRoles
from waitlist.data.perm import perm_accounts, perm_settings, perm_admin, perm_leadership
from waitlist.permissions import perm_manager
from waitlist.signal.signals import send_account_created, send_roles_changed, send_account_status_change
from waitlist.storage.database import Account, Character, Role, linked_chars
from waitlist.utility.eve_id_utils import get_character_by_name
from waitlist.utility.settings import sget_resident_mail, sget_tbadge_mail, sget_other_mail, sget_other_topic, \
    sget_tbadge_topic, sget_resident_topic
from waitlist.utility.utils import get_random_token

bp = Blueprint('accounts', __name__)
logger = logging.getLogger(__name__)


@bp.route("/", methods=["GET", "POST"])
@login_required
@perm_accounts.require(http_exception=401)
def accounts():
    if request.method == "POST":
        acc_name = request.form['account_name']

        acc_roles = request.form.getlist('account_roles')

        char_name = request.form['default_char_name']
        char_name = char_name.strip()

        note = request.form['change_note'].strip()

        char_id = get_character_id_from_name(char_name)
        if char_id == 0:
            flash("This Character does not exist!")
        else:
            acc = Account()
            acc.username = acc_name

            acc.login_token = get_random_token(16)

            if len(acc_roles) > 0:
                db_roles = db.session.query(Role).filter(or_(Role.name == name for name in acc_roles)).all()
                for role in db_roles:
                    acc.roles.append(role)

            db.session.add(acc)

            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()

            if character is None:
                char_info = get_char_info_for_character(char_id)
                character = Character()
                character.eve_name = char_info.characterName
                character.id = char_id

            acc.characters.append(character)

            db.session.flush()

            acc.current_char = char_id

            db.session.commit()
            send_account_created(accounts, acc.id, current_user.id, acc_roles, 'Creating account. ' + note)

    roles = db.session.query(Role).order_by(Role.name).all()
    accs = db.session.query(Account).order_by(asc(Account.disabled)).order_by(Account.username).all()
    mails = {
        'resident': [sget_resident_mail(), sget_resident_topic()],
        'tbadge': [sget_tbadge_mail(), sget_tbadge_topic()],
        'other': [sget_other_mail(), sget_other_topic()]
    }

    return render_template("settings/accounts.html", roles=roles, accounts=accs, mails=mails)


@bp.route("/edit", methods=["POST"])
@login_required
@perm_accounts.require(http_exception=401)
def account_edit():
    acc_id = int(request.form['account_id'])
    acc_name = request.form['account_name']

    note = request.form['change_note'].strip()

    acc_roles = request.form.getlist('account_roles')

    char_name = request.form['default_char_name']
    char_name = char_name.strip()
    if char_name == "":
        char_name = None

    acc = db.session.query(Account).filter(Account.id == acc_id).first()
    if acc is None:
        return flask.abort(400)

    if acc.username != acc_name:
        acc.username = acc_name

    # if there are roles, add new ones, remove the ones that aren't there
    if len(acc_roles) > 0:
        roles_new = {}
        for r in acc_roles:
            roles_new[r] = True

        # db_roles = session.query(Role).filter(or_(Role.name == name for name in acc_roles)).all()
        roles_to_remove = []
        for role in acc.roles:
            if role.name in roles_new:
                del roles_new[role.name]  # remove because it is already in the db
            else:
                # remove the roles because it not submitted anymore
                # only remove admin if current user is an admin
                if role.name == WTMRoles.admin and not perm_manager.get_permission('admin').can():
                    continue
                roles_to_remove.append(role)  # mark for removal

        for role in roles_to_remove:
            acc.roles.remove(role)

        # if it is not an admin remove admin role from new roles
        if not perm_manager.get_permission('admin').can():
           if 'admin' in roles_new:
               del roles_new['admin']

        # add remaining roles
        if len(roles_new) > 0:
            new_db_roles = db.session.query(Role).filter(or_(Role.name == name for name in roles_new))
            for role in new_db_roles:
                acc.roles.append(role)
        if len(roles_new) > 0 or len(roles_to_remove) >0:
            send_roles_changed(account_edit, acc.id, current_user.id, [x for x in roles_new],
                           [x.name for x in roles_to_remove], note)
    else:
        # make sure all roles are removed
        roles_to_remove = []
        for role in acc.roles:
            # only remove admin if current user is an admin
            if role.name == WTMRoles.admin and not perm_manager.get_permission('admin').can():
                continue
            roles_to_remove.append(role)

        if len(roles_to_remove) > 0:
            for role in roles_to_remove:
                acc.roles.remove(role)
            db.session.flush()
            send_roles_changed(account_edit, acc.id, current_user.id, [x.name for x in roles_to_remove], [], note)

    if char_name is not None:
        char_id = get_character_id_from_name(char_name)
        if char_id == 0:
            flash("Character " + char_name + " does not exist!")
        else:
            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()

            if character is None:
                # lets make sure we have the correct name (case)
                char_info = get_char_info_for_character(char_id)
                character = Character()
                character.eve_name = char_info.characterName
                character.id = char_id

            # check if character is linked to this account
            link = db.session.query(linked_chars) \
                .filter((linked_chars.c.id == acc_id) & (linked_chars.c.char_id == char_id)).first()
            if link is None:
                acc.characters.append(character)

            db.session.flush()
            acc.current_char = char_id

    db.session.commit()
    return redirect(url_for('.accounts'), code=303)


@bp.route("/self_edit", methods=["POST"])
@login_required
@perm_settings.require(http_exception=401)
def account_self_edit():
    acc_id = current_user.id

    char_name = request.form['default_char_name']
    char_name = char_name.strip()
    if char_name == "":
        char_name = None

    acc = db.session.query(Account).filter(Account.id == acc_id).first()
    if acc is None:
        return flask.abort(400)

    if char_name is not None:
        char_id = get_character_id_from_name(char_name)

        if char_id == 0:
            flash("Character " + char_name + " does not exist!")
        else:

            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()

            if character is None:
                # lets make sure we have the correct name (case)
                char_info = get_char_info_for_character(char_id)
                character = Character()
                character.eve_name = char_info.characterName
                character.id = char_id

            # check if character is linked to this account
            link = db.session.query(linked_chars) \
                .filter((linked_chars.c.id == acc_id) & (linked_chars.c.char_id == char_id)).first()
            if link is None:
                acc.characters.append(character)

            db.session.flush()
            if acc.current_char != char_id:
                # remove all the access tokens
                if acc.ssoToken is not None:
                    db.session.delete(acc.ssoToken)
                acc.current_char = char_id

    db.session.commit()
    return redirect(url_for('.account_self'), code=303)


@bp.route("/self", methods=["GET"])
@login_required
@perm_settings.require(http_exception=401)
def account_self():
    acc = db.session.query(Account).filter(Account.id == current_user.id).first()
    return render_template("settings/self.html", account=acc)


@bp.route("/api/account/disabled", methods=['POST'])
@login_required
@perm_accounts.require(http_exception=401)
def account_disabled():
    accid: int = int(request.form['id'])
    acc: Account = db.session.query(Account).filter(Account.id == accid).first()
    status: Union(str, bool) = request.form['disabled']
    send_account_status_change(account_disabled, acc.id, current_user.id, status)
    logger.info("%s sets account %s to %s", current_user.username, acc.username, status)
    if status == 'false':
        status = False
    else:
        status = True

    acc.disabled = status
    db.session.commit()
    return "OK"


@bp.route("/api/account/<int:acc_id>", methods=["DELETE"])
@login_required
@perm_admin.require(http_exception=401)
def api_account_delete(acc_id: int) -> Response:
    db.session.query(Account).filter(Account.id == acc_id).delete()
    db.session.commit()
    return flask.jsonify(status="OK")


@bp.route("/accounts/import/accounts", methods=["POST"])
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


@bp.route('/accounts/downloadlist/cvs')
@login_required
@perm_manager.require('leadership')
def accounts_download_csv() -> Response:
    def iter_accs(data):
        for account in data:
            for ci, char in enumerate(account.characters):
                if ci > 0:
                    yield ", " + char.eve_name
                else:
                    yield char.eve_name
            yield '\n'

    # noinspection PyPep8
    accs = db.session.query(Account).options(joinedload('characters')).join(Account.roles).filter(
        ((Role.name == WTMRoles.fc) | (Role.name == WTMRoles.lm)) & (Account.disabled == False)).order_by(
        Account.username).all()

    response = Response(iter_accs(accs), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=accounts.csv'
    return response

add_menu_entry('accounts.accounts', 'Accounts', perm_accounts.can)
add_menu_entry('accounts.account_self', 'Own Settings', lambda: True)
