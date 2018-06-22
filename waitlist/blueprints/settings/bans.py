import logging
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user, login_required
from sqlalchemy import asc

from waitlist.utility import outgate
from waitlist import db
from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager
from waitlist.storage.database import Ban, Whitelist, Character
from waitlist.utility.eve_id_utils import get_character_by_name
from waitlist.utility.utils import get_info_from_ban
from flask_babel import lazy_gettext, gettext
from waitlist.utility.outgate.exceptions import ApiException

bp = Blueprint('bans', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('bans_edit')
perm_manager.define_permission('bans_edit_multiple')
perm_manager.define_permission('bans_custom_name')
perm_manager.define_permission('bans_custom_reason')

perm_custom_name = perm_manager.get_permission('bans_custom_name')
perm_custom_reason = perm_manager.get_permission('bans_custom_reason')


@bp.route("/", methods=["GET"])
@login_required
@perm_manager.require('bans_edit')
def bans():
    db_bans = db.session.query(Ban).order_by(asc(Ban.name)).all()
    return render_template("settings/bans.html", bans=db_bans)


@bp.route("/bans_change", methods=["POST"])
@login_required
@perm_manager.require('bans_edit_multiple')
def bans_change():
    action = request.form['change']  # ban, unban
    target = request.form['target']  # name of target
    reason = ''
    if action == "ban":
        reason = request.form['reason']  # reason for ban

    targets = target.split("\n")

    try:
        # pre-cache names for a faster api to not hit request limit
        names_to_cache = []
        for line in targets:
            line = line.strip()
            ban_name, _, ban_admin = get_info_from_ban(line)
            names_to_cache.append(ban_name)
            if ban_admin is not None:
                names_to_cache.append(ban_admin)

        if action == "ban":
            for target in targets:
                target = target.strip()

                ban_name, ban_reason, ban_admin = get_info_from_ban(target)

                if ban_reason is None:
                    ban_reason = reason

                if ban_admin is None:
                    ban_admin = current_user.get_eve_name()

                logger.info("Banning %s for %s by %s as %s.", ban_name, ban_reason, ban_admin, current_user.username)
                ban_id = outgate.character.get_char_corp_all_id_by_name(ban_name)
                admin_char = get_character_by_name(ban_admin)
                if ban_id is None:
                    logger.error("Did not find ban target %s", ban_name)
                    flash(gettext("Could not find Character %(ban_name)s",
                                  ban_name=ban_name), "danger")
                    continue

                admin_id = admin_char.get_eve_id()

                if ban_id is None or admin_id is None:
                    logger.error("Failed to correctly parse: %", target)
                    flash(gettext("Failed to correctly parse %(target)s",
                                  target=target), "danger")
                    continue

                # check if ban already there
                if db.session.query(Ban).filter(Ban.id == ban_id).count() == 0:
                    # ban him
                    new_ban = Ban()
                    new_ban.id = ban_id
                    new_ban.name = ban_name
                    new_ban.reason = ban_reason
                    new_ban.admin = admin_id
                    db.session.add(new_ban)
                    db.session.commit()
        elif action == "unban":
            for target in targets:
                target = target.strip()
                logger.info("%s is unbanning %s", current_user.username, target)
                eve_id = outgate.character.get_char_corp_all_id_by_name(target)
                if eve_id is None:
                    flash(gettext("Character/Corp/Alliance %(target)s does not exist!", target=target), 'danger')
                else:
                    # check that there is a ban
                    if db.session.query(Ban).filter(Ban.id == eve_id).count() > 0:
                        db.session.query(Ban).filter(Ban.id == eve_id).delete()
                        db.session.commit()
    except ApiException as e:
        flash(gettext("Could not execute action, ApiException %(ex)s", e),
              'danger')

    return redirect(url_for(".bans"))


@bp.route("/bans_change_single", methods=["POST"])
@login_required
@perm_manager.require('bans_edit')
def bans_change_single():
    try:
        action = request.form['change']  # ban, unban
        target = request.form['target']  # name of target
    
        target = target.strip()
    
        ban_admin = current_user.get_eve_name()
        ban_name = target
    
        if action == "ban":
            reason = request.form['reason']  # reason for ban
            ban_char = get_character_by_name(ban_name)
            admin_char = get_character_by_name(ban_admin)
            logger.info("Banning %s for %s as %s.", ban_name, reason, current_user.username)
            if ban_char is None:
                logger.error("Did not find ban target %s", ban_name)
                flash(gettext("Could not find Character %(name)s", name=ban_name),
                      "danger")
                return
    
            eve_id = ban_char.get_eve_id()
            admin_id = admin_char.get_eve_id()
    
            if eve_id is None or admin_id is None:
                logger.error("Failed to correctly parse: %", target)
                flash(gettext("Failed to correctly parse %(target)s",
                              target=target),
                      "danger")
                return
    
            # check if ban already there
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
            eve_id = outgate.character.get_char_corp_all_id_by_name(target)
            if eve_id is None:
                flash(gettext("Character/Corp/Alliance %(target)s does not exist!", target=target), 'danger')
            else:
                # check that there is a ban
                if db.session.query(Ban).filter(Ban.id == eve_id).count() > 0:
                    db.session.query(Ban).filter(Ban.id == eve_id).delete()
                    db.session.commit()
    except ApiException as e:
        flash(gettext("Could not execute action, ApiException %(ex)s", e),
              'danger')

    return redirect(url_for(".bans"))


@bp.route("/bans_unban", methods=["POST"])
@login_required
@perm_manager.require('bans_edit')
def bans_unban_single():
    target = request.form['target']  # name of target
    target = target.strip()
    logger.info("%s is unbanning %s", current_user.username, target)
    try:
        eve_id = outgate.character.get_char_corp_all_id_by_name(target)
        if eve_id is None:
            flash(gettext("Character/Corp/Alliance %(target)s does not exist!",
                          target=target), 'danger')
        else:
            # check that there is a ban
            if db.session.query(Ban).filter(Ban.id == eve_id).count() > 0:
                db.session.query(Ban).filter(Ban.id == eve_id).delete()
                db.session.commit()
    except ApiException as e:
        flash(gettext("Could not execute action, ApiException %(ex)s", e),
              'danger')

    return redirect(url_for(".bans"))


@bp.route("/whitelist", methods=["GET"])
@login_required
@perm_manager.require('bans_edit')
def whitelist():
    whitelistings = db.session.query(Whitelist).join(Character, (Whitelist.characterID == Character.id)).order_by(
        asc(Character.eve_name)).all()
    return render_template("settings/whitelist.html", wl=whitelistings)


@bp.route("/whitelist_change", methods=["POST"])
@login_required
@perm_manager.require('bans_edit_multiple')
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

    try:
        if action == "whitelist":
            for target in targets:
                whitelist_by_name(target, reason)

        elif action == "unwhitelist":
            for target in targets:
                unwhitelist_by_name(target)
    except ApiException as e:
        flash(gettext("Could not execute action, ApiException %(ex)s", e),
              'danger')

    return redirect(url_for(".whitelist"))


'''
@param ban_info: a eve character name, or copy from ingame chat window
'''


def whitelist_by_name(whitelist_info, reason=""):
    target = whitelist_info.strip()

    wl_name, wl_reason, wl_admin = get_info_from_ban(target)

    if wl_reason is None or not perm_custom_reason.can():
        wl_reason = reason

    if wl_admin is None or not perm_custom_name.can():
        wl_admin = current_user.get_eve_name()

    logger.info("Whitelisting %s for %s by %s as %s.", wl_name, wl_reason, wl_admin, current_user.username)
    wl_char = get_character_by_name(wl_name)
    admin_char = get_character_by_name(wl_admin)
    if wl_char is None:
        logger.error("Did not find whitelist target %s", wl_name)
        flash(gettext("Could not find Character %(wl_name)s for whitelisting",
                      wl_name=wl_name), "danger")
        return

    eve_id = wl_char.get_eve_id()
    admin_id = admin_char.get_eve_id()

    if eve_id is None or admin_id is None:
        logger.error("Failed to correctly parse: %", target)
        flash(gettext("Failed to correctly parse %(target)s", target=target),
              "danger")
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
    eve_id = outgate.character.get_char_corp_all_id_by_name(target)
    if eve_id is None:
        flash(gettext("Character/Corp/Alliance %(target)s does not exist!",
                      target=target),
              'danger')
    else:
        # check that there is a ban
        if db.session.query(Whitelist).filter(Whitelist.characterID == eve_id).count() > 0:
            db.session.query(Whitelist).filter(Whitelist.characterID == eve_id).delete()
            db.session.commit()


@bp.route("/whitelist_change_single", methods=["POST"])
@login_required
@perm_manager.require('bans_edit')
def whitelist_change_single():
    action = request.form['change']  # whitelist, unwhitelist
    target = request.form['target']  # name of target

    target = target.strip()

    try:
        if action == "whitelist":
            reason = request.form['reason']  # reason for ban
            whitelist_by_name(target, reason)
        elif action == "unwhitelist":
            unwhitelist_by_name(target)
    except ApiException as e:
        flash(gettext("Could not execute action, ApiException %(ex)s", e),
              'danger')

    return redirect(url_for(".withelist"))


@bp.route("/whitelist_unlist", methods=["POST"])
@login_required
@perm_manager.require('bans_edit')
def whitelist_unlist():
    target = request.form['target']  # name of target
    target = target.strip()
    try:
        unwhitelist_by_name(target)
    except ApiException as e:
        flash(gettext("Could not execute action, ApiException %(ex)s", e),
              'danger')

    return redirect(url_for(".whitelist"))


add_menu_entry('bans.bans', lazy_gettext('Bans'), perm_manager.get_permission('bans_edit').can)
add_menu_entry('bans.whitelist', lazy_gettext('Whitelist'), perm_manager.get_permission('bans_edit').can)
