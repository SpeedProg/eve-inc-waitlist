import logging
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user, login_required
from sqlalchemy import asc

from waitlist import db
from waitlist.data.eve_xml_api import get_character_id_from_name
from waitlist.data.perm import perm_bans, perm_leadership
from waitlist.storage.database import Ban
from waitlist.utility.eve_id_utils import get_character_by_name
from waitlist.utility.utils import get_info_from_ban

bp = Blueprint('bans', __name__)
logger = logging.getLogger(__name__)


@bp.route("/bans", methods=["GET"])
@login_required
@perm_bans.require(http_exception=401)
def bans():
    db_bans = db.session.query(Ban).order_by(asc(Ban.name)).all()
    return render_template("settings/bans.html", bans=db_bans)


@bp.route("/bans_change", methods=["POST"])
@login_required
@perm_leadership.require(http_exception=401)
def bans_change():
    action = request.form['change']  # ban, unban
    target = request.form['target']  # name of target
    reason = ''
    if action == "ban":
        reason = request.form['reason']  # reason for ban

    targets = target.split("\n")

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

            # check if ban already there
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

    return redirect(url_for(".bans"))


@bp.route("/bans_change_single", methods=["POST"])
@login_required
@perm_bans.require(http_exception=401)
def bans_change_single():
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
            flash("Could not find Character " + ban_name, "danger")
            return

        eve_id = ban_char.get_eve_id()
        admin_id = admin_char.get_eve_id()

        if eve_id is None or admin_id is None:
            logger.error("Failed to correctly parse: %", target)
            flash("Failed to correctly parse " + target, "danger")
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
        eve_id = get_character_id_from_name(target)
        if eve_id == 0:
            flash("Character " + target + " does not exist!")
        else:
            # check that there is a ban
            if db.session.query(Ban).filter(Ban.id == eve_id).count() > 0:
                db.session.query(Ban).filter(Ban.id == eve_id).delete()
                db.session.commit()

    return redirect(url_for(".bans"))


@bp.route("/bans_unban", methods=["POST"])
@login_required
@perm_bans.require(http_exception=401)
def bans_unban_single():
    target = request.form['target']  # name of target
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

    return redirect(url_for(".bans"))