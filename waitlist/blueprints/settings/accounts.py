import logging
from datetime import timedelta, datetime
from typing import Union, Optional, List

import flask
from flask import Blueprint, session
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required, current_user
from sqlalchemy import asc
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from waitlist import db
from waitlist.blueprints.fc_sso import get_sso_redirect, add_sso_handler
from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager
from waitlist.permissions.manager import StaticPermissions, StaticRoles
from waitlist.signal.signals import send_account_created, send_roles_changed, send_account_status_change
from waitlist.sso import authorize, who_am_i
from waitlist.storage.database import Account, Character, Role, linked_chars, APICacheCharacterInfo, SSOToken
from waitlist.utility import outgate, config
from waitlist.utility.login import invalidate_all_sessions_for_given_user
from waitlist.utility.manager.owner_hash_check_manager import OwnerHashCheckManager
from waitlist.utility.settings import sget_resident_mail, sget_tbadge_mail, sget_other_mail, sget_other_topic, \
    sget_tbadge_topic, sget_resident_topic
from waitlist.utility.utils import get_random_token

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
    clean_alt_list()
    roles = db.session.query(Role).order_by(Role.name).all()
    accs = db.session.query(Account).order_by(asc(Account.disabled)).order_by(Account.username).all()
    mails = {
        'resident': [sget_resident_mail(), sget_resident_topic()],
        'tbadge': [sget_tbadge_mail(), sget_tbadge_topic()],
        'other': [sget_other_mail(), sget_other_topic()]
    }

    return render_template("settings/accounts.html", roles=roles, accounts=accs, mails=mails)


def clean_alt_list() -> None:
    """
    Removes links between accounts and characters if
     there is a token
     but the token expired
     or the owner_hash changed (this should expire the token!)
    if there is no token for the character at all, the character is keept
    """
    accs: List[Account] = db.session.query(Account).all()
    for acc in accs:
        for char in acc.characters:
            if OwnerHashCheckManager.is_auth_valid_for_account_character_pair(acc, char):
                continue

            token: Optional[SSOToken] = acc.get_token_for_charid(char.id)
            # if there is no token for this account/character combination we don't need to do anything
            if token is None:
                continue

            # the auth token is not valid AND we have a token
            # remove the invalid toekn
            db.session.delete(token)

    db.session.commit()


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

    acc: Account = db.session.query(Account).filter(Account.id == acc_id).first()
    if acc is None:
        return flask.abort(400)

    if char_name is not None and (current_user.get_eve_name() is None or char_name != current_user.get_eve_name()):
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
                if config.require_auth_for_chars:
                    # this is a new link, lets redirect him to check if he owns the character after we saved the charid
                    session['link_charid'] = character.id
                    return get_sso_redirect("alt_verification", 'publicData')
                else:
                    acc.characters.append(character)

            db.session.flush()
            if acc.current_char != char_id:
                # we have a link and it is not the current char
                if config.require_auth_for_chars:
                    # we need authentication for char change so lets see if the token works
                    auth_token: SSOToken = acc.get_a_sso_token_with_scopes([], char_id)

                    # we need new auth
                    if auth_token is None:
                        logger.debug("Could not find a valid authorization for this character")
                        session['link_charid'] = character.id
                        return get_sso_redirect("alt_verification", 'publicData')

                    auth_info = who_am_i(auth_token)
                    # if we don't have this the token was invalid
                    if 'CharacterOwnerHash' not in auth_info:
                        logger.debug("CharacterOwnerHash was not in authorization info")
                        db.session.delete(auth_token)
                        db.session.commit()
                        # let them re authenticate
                        session['link_charid'] = character.id
                        return get_sso_redirect("alt_verification", 'publicData')

                    if auth_info['CharacterOwnerHash'] != character.owner_hash:
                        # owner hash does not match
                        db.session.delete(auth_token)
                        db.session.commit()
                        session['link_charid'] = character.id
                        logger.debug("Character owner_owner hash did not match")
                        return get_sso_redirect("alt_verification", 'publicData')

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
    # noinspection PyPep8
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


@login_required
@perm_manager.require('settings_access')
def alt_verification_handler(code: str) -> None:
    # this throws exception and exists this function
    if current_user.type != 'account':
        flask.abort(403, "You are not on an account.")

    auth = authorize(code)

    access_token = auth['access_token']
    refresh_token = auth['refresh_token']
    exp_in = int(auth['expires_in'])
    auth_token: SSOToken = SSOToken(accountID=current_user.id, refresh_token=refresh_token,
                                    access_token=access_token,
                                    access_token_expires=(datetime.utcnow() + timedelta(seconds=exp_in)))

    auth_info = who_am_i(auth_token)
    char_id = int(auth_info['CharacterID'])
    owner_hash = auth_info['CharacterOwnerHash']
    scopes: str = auth_info['Scopes']
    auth_token.characterID = char_id
    # if he authed the char he told us
    if session['link_charid'] is not None and session['link_charid'] == char_id:
        logger.debug("Updating Token for %s char_id=%s", current_user, char_id)
        session.pop('link_charid')  # remove info from session
        auth_token.update_token_data(scopes=scopes)
        db.session.merge(auth_token)
        db.session.commit()

        # make sure the char is not already linked to the account
        for character in current_user.characters:
            if character.id == char_id:  # we are already linked to the char
                # if it is not set as active char set it
                if current_user.current_char != char_id:
                    current_user.current_char = char_id

                # we need to check and maybe update owner hash
                if character.owner_hash is None or character.owner_hash == '':
                    # first time accessing this character
                    logger.info("Setting owner_hash for %s the first time", character)
                    character.owner_hash = owner_hash

                elif character.owner_hash != owner_hash:
                    # the owner changed
                    logger.info("Setting new owner_hash for %s, invalidating all existing sessions", character)
                    invalidate_all_sessions_for_given_user(character)

                db.session.commit()
                return redirect(url_for('accounts.account_self'), code=303)

        # we need to add the char
        # try if he is already in db
        character = db.session.query(Character).filter(Character.id == char_id).first()

        if character is None:
            # lets make sure we have the correct name (case)
            char_info: APICacheCharacterInfo = outgate.character.get_info(char_id)
            character = Character()
            character.eve_name = char_info.characterName
            character.id = char_id
            character.owner_hash = owner_hash
        else:
            if character.owner_hash is None or character.owner_hash == '':
                # first time accessing this character
                logger.info("Setting owner_hash for %s the first time", character)
                character.owner_hash = owner_hash

            if character.owner_hash != owner_hash:
                character.owner_hash = owner_hash
                invalidate_all_sessions_for_given_user(character)
                logger.info("Setting new owner_hash for %s, invalidating all existing sessions", character)

        # delete any existing links (to other accounts)
        db.session.query(linked_chars) \
            .filter((linked_chars.c.id != current_user.id)
                    & (linked_chars.c.char_id == char_id)).delete(synchronize_session=False)

        db.session.commit()

        # add the new link
        current_user.characters.append(character)
        db.session.flush()
        if current_user.current_char != char_id:
            current_user.current_char = char_id

        db.session.commit()
        flash(f'Alt {character.eve_name} was added', 'info')
        return redirect(url_for('accounts.account_self'), code=303)
    else:
        flask.abort(400, 'Could not confirm your authorisation of the alt,'
                         ' most likely you authenticated a wrong character.')


add_sso_handler('alt_verification', alt_verification_handler)
