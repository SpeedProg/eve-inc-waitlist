import logging
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
from pyswagger.contrib.client import flask
from sqlalchemy import asc
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from waitlist import db
from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager
from waitlist.permissions.manager import StaticPermissions, StaticRoles
from waitlist.signal.signals import send_account_created, send_roles_changed, send_account_status_change
from waitlist.storage.database import Account, Character, Role, linked_chars, APICacheCharacterInfo
from waitlist.utility.settings import sget_resident_mail, sget_tbadge_mail, sget_other_mail, sget_other_topic, \
    sget_tbadge_topic, sget_resident_topic
from waitlist.utility.utils import get_random_token

from waitlist.utility import outgate

bp = Blueprint('accounts', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('include_in_accountlist')
perm_manager.define_permission('accounts_edit')
perm_manager.define_permission('settings_access')
perm_manager.define_permission('admin')
perm_manager.define_permission('accounts_download_list')


@bp.route("/", methods=["GET", "POST"])
@login_required
@perm_manager.require('accounts_edit')
def accounts():
    if request.method == "POST":
        acc_name = request.form['account_name']

        acc_roles = request.form.getlist('account_roles')

        char_name = request.form['default_char_name']
        char_name = char_name.strip()

        note = request.form['change_note'].strip()

        char_info = outgate.character.get_info_by_name(char_name)
        if char_info is None:
            flash(f"A Character named {char_name} does not exist!")
        else:
            char_id = char_info.id
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
                char_info: APICacheCharacterInfo = outgate.character.get_info(char_id)
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
@perm_manager.require('accounts_edit')
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
                if role.name == StaticRoles.ADMIN and not perm_manager.get_permission(StaticPermissions.ADMIN).can():
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
        if len(roles_new) > 0 or len(roles_to_remove) > 0:
            send_roles_changed(account_edit, acc.id, current_user.id, [x for x in roles_new],
                               [x.name for x in roles_to_remove], note)
    else:
        # make sure all roles are removed
        roles_to_remove = []
        for role in acc.roles:
            # only remove admin if current user is an admin
            if role.name == StaticRoles.ADMIN and not perm_manager.get_permission(StaticPermissions.ADMIN).can():
                continue
            roles_to_remove.append(role)

        if len(roles_to_remove) > 0:
            for role in roles_to_remove:
                acc.roles.remove(role)
            db.session.flush()
            send_roles_changed(account_edit, acc.id, current_user.id, [], [x.name for x in roles_to_remove], note)

    if char_name is not None:
        char_info = outgate.character.get_info_by_name(char_name)
        if char_info is None:
            flash(f"Character with name {char_name} could not be found!")
        else:
            char_id = char_info.id
            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()

            if character is None:
                # lets make sure we have the correct name (case)
                char_info: APICacheCharacterInfo = outgate.character.get_info(char_id)
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
@perm_manager.require('settings_access')
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
        char_info = outgate.character.get_info_by_name(char_name)

        if char_info is None:
            flash("Character with name {char_name} could not be found!")
        else:
            char_id = char_info.id
            # find out if there is a character like that in the database
            character = db.session.query(Character).filter(Character.id == char_id).first()

            if character is None:
                # lets make sure we have the correct name (case)
                char_info: APICacheCharacterInfo = outgate.character.get_info(char_id)
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
@perm_manager.require('settings_access')
def account_self():
    acc = db.session.query(Account).filter(Account.id == current_user.id).first()
    return render_template("settings/self.html", account=acc)


@bp.route("/api/account/disabled", methods=['POST'])
@login_required
@perm_manager.require('settings_access')
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
@perm_manager.require('admin')
def api_account_delete(acc_id: int) -> Response:
    db.session.query(Account).filter(Account.id == acc_id).delete()
    db.session.commit()
    return flask.jsonify(status="OK")


@bp.route('/accounts/downloadlist/cvs')
@login_required
@perm_manager.require('accounts_download_list')
def accounts_download_csv() -> Response:
    def iter_accs(data):
        for account in data:
            for ci, char in enumerate(account.characters):
                if ci > 0:
                    yield ", " + char.eve_name
                else:
                    yield char.eve_name
            yield '\n'

    permission = perm_manager.get_permission('include_in_accountlist')
    include_check = (Account.disabled == False)
    role_check = None
    for role_need in permission.needs:
        if role_need.method != 'role':
            continue
        if role_check is None:
            role_check = (Role.name == role_need.value)
        else:
            role_check = role_check | (Role.name == role_need.value)

    include_check = (include_check & role_check)

    # noinspection PyPep8
    accs = db.session.query(Account).options(joinedload('characters')).join(Account.roles).filter(
        include_check ).order_by(
        Account.username).all()

    response = Response(iter_accs(accs), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=accounts.csv'
    return response

add_menu_entry('accounts.accounts', 'Accounts', perm_manager.get_permission('accounts_edit').can)
add_menu_entry('accounts.account_self', 'Own Settings', lambda: True)
