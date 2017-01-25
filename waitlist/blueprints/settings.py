from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.data.perm import perm_admin, perm_settings, perm_officer,\
    perm_management, perm_accounts, perm_dev, perm_leadership,\
    perm_fleetlocation, perm_bans
from flask.templating import render_template
from flask.globals import request
from sqlalchemy import or_, asc
from waitlist.storage.database import Account, Role, Character,\
    linked_chars, Ban, Constellation, IncursionLayout, SolarSystem, Station,\
    WaitlistEntry, WaitlistGroup, Whitelist, TeamspeakDatum, Shipfit, InvType
import flask
from waitlist.data.eve_xml_api import get_character_id_from_name,\
    eve_api_cache_char_ids
from werkzeug.utils import redirect, secure_filename
from flask.helpers import url_for, flash
from waitlist.utility.utils import get_random_token, get_info_from_ban
from waitlist.base import db, app
from waitlist.utility.eve_id_utils import get_constellation, get_system,\
    get_station, get_character_by_name
from os import path
import os
from bz2 import BZ2File
from waitlist.utility import sde
from flask import jsonify
import csv
from waitlist.data.names import WTMRoles
from waitlist.utility.settings import settings
from waitlist.utility.settings.settings import sget_active_ts_id,\
    sset_active_ts_id, sget_resident_mail, sget_tbadge_mail, sget_resident_topic,\
    sget_tbadge_topic, sget_other_mail, sget_other_topic
from waitlist.ts3.connection import change_connection
from datetime import datetime, timedelta
from waitlist.data.sse import StatusChangedSSE, sendServerSentEvent
from waitlist.utility import config
from waitlist.signal.signals import sendRolesChanged, sendAccountCreated
from waitlist.permissions import perm_manager
from flask.wrappers import Response
from sqlalchemy.orm import joinedload

bp_settings = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

cache = {};

def createCacheItem(data, expire_in_s):
    return {'data': data, 'datetime': (datetime.utcnow() + timedelta(seconds=expire_in_s))}

def hasCacheItem(key):
    if not key in cache:
        return False
    
    if cache[key]['datetime'] < datetime.utcnow():
        return False
    return True

def getCacheItem(key):
    if not key in cache:
        return None
    return cache[key]

def addItemToCache(key, item):
    cache[key] = item

@bp_settings.route("/")
@login_required
@perm_settings.require(http_exception=401)
def overview():
    shipStatsQuery = '''
SELECT shipType, COUNT(name)
FROM (
    SELECT DISTINCT invtypes.typeName AS shipType, characters.eve_name AS name
    FROM fittings
    JOIN invtypes ON fittings.ship_type = invtypes.typeID
    JOIN comp_history_fits ON fittings.id = comp_history_fits.fitID
    JOIN comp_history ON comp_history_fits.historyID = comp_history.historyID
    JOIN characters ON comp_history.targetID = characters.id
    WHERE
     (
     comp_history.action = 'comp_mv_xup_etr'
     OR
     comp_history.action = 'comp_mv_xup_fit'
     )
    AND DATEDIFF(NOW(),comp_history.TIME) < 30
) AS temp
GROUP BY shipType
ORDER BY COUNT(name) DESC
LIMIT 15;
    '''
    
    approvedFitsByFCQuery = '''
    SELECT name, COUNT(fitid)
FROM (
    SELECT DISTINCT accounts.username AS name, comp_history_fits.id as fitid
    FROM fittings
    JOIN invtypes ON fittings.ship_type = invtypes.typeID
    JOIN comp_history_fits ON fittings.id = comp_history_fits.fitID
    JOIN comp_history ON comp_history_fits.historyID = comp_history.historyID
    JOIN accounts ON comp_history.sourceID = accounts.id
    JOIN characters ON comp_history.targetID = characters.id
    WHERE
     (
     comp_history.action = 'comp_mv_xup_etr'
     OR
     comp_history.action = 'comp_mv_xup_fit'
     )
    AND DATEDIFF(NOW(),comp_history.TIME) < 7
) AS temp
GROUP BY name
ORDER BY COUNT(fitid) DESC
LIMIT 15;
    '''
    
    shipStats1DayQuery = '''
    SELECT shipType, COUNT(name)
FROM (
    SELECT DISTINCT invtypes.typeName AS shipType, characters.eve_name AS name
    FROM fittings
    JOIN invtypes ON fittings.ship_type = invtypes.typeID
    JOIN comp_history_fits ON fittings.id = comp_history_fits.fitID
    JOIN comp_history ON comp_history_fits.historyID = comp_history.historyID
    JOIN characters ON comp_history.targetID = characters.id
    WHERE
     (
     comp_history.action = 'comp_mv_xup_etr'
     OR
     comp_history.action = 'comp_mv_xup_fit'
     )
    AND TIMESTAMPDIFF(HOUR, comp_history.time, NOW()) < 24
) AS temp
GROUP BY shipType
ORDER BY COUNT(name) DESC
LIMIT 15;
    '''
    
    shipStats15Days = getQueryResult('shipStats', shipStatsQuery, 2, 3600)
    approvedFitsByFCResult = getQueryResult('approvedFits30Days', approvedFitsByFCQuery, 2, 3600)
    shipStats1Day = getQueryResult('shipStats1Day', shipStats1DayQuery, 2, 3600)
    
    stats = [
        createTableCellRow(
            createTableCellData('Top 15 approved distinct Hull/Character combinations last 30 days', ['Hull', 'Amount'], shipStats15Days),
            createTableCellData('15 Most Active Command Core Members over last 7days', ['Account Name', 'Amount'], approvedFitsByFCResult, [False, True])
            ),
        createTableCellRow(
            createTableCellData('Top 15 approved distinct Hull/Character combination last 24 hours', ['Hull', 'Amount'], shipStats1Day),
            createTableCellData('If you have ideas for other stats, use the feedback function.', [], [], [])
            )
        ]
    
    return render_template('settings/overview.html', stats=stats)

def createTableCellRow(left, right):
    return (left, right)

def createTableCellData(desc, column_names, data, hide_rows=[]):
    if len(data) >= 1 and len(data[0]) != len(column_names):
        raise ValueError("len(column_names) != len(data[0])")
    if len(hide_rows) == 0:
        print("Generating default hiding list")
        hide_rows = [False for _ in xrange(len(column_names))]
    elif len(hide_rows) != len(column_names):
        raise ValueError("When hide_rows is specified it needs to be of the same length as the defined columns")
    
    return (desc, column_names, data, hide_rows)

def getQueryResult(name, query, columnCount, cacheTimeSeconds):
    result = []
    if hasCacheItem(name):
        cacheItem = getCacheItem(name)
        result = cacheItem['data']
    else:
        db_result = db.engine.execute(query)
        for row in db_result:
            rowList = []
            for idx in xrange(0, columnCount):
                rowList.append(row[idx])
            result.append(rowList)
        addItemToCache(name, createCacheItem(result, cacheTimeSeconds))
    return result
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
        
        note = request.form['change_note'].strip()
        
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
            sendAccountCreated(accounts, acc.id, current_user.id, acc_roles, 'Creating account. ' + note)

    roles = db.session.query(Role).order_by(Role.name).all();
    accs = db.session.query(Account).order_by(asc(Account.disabled)).order_by(Account.username).all()
    mails = {
             'resident': [sget_resident_mail(), sget_resident_topic()],
             'tbadge': [sget_tbadge_mail(), sget_tbadge_topic()],
             'other': [sget_other_mail(), sget_other_topic()]
             }

    return render_template("settings/accounts.html", roles=roles, accounts=accs, mails=mails)

@bp_settings.route('/fmangement')
@login_required
@perm_management.require(http_exception=401)
def fleet():
    groups = db.session.query(WaitlistGroup).all()
    return render_template("settings/fleet.html", user=current_user, groups=groups, scramble=config.scramble_names)


@bp_settings.route("/account_edit", methods=["POST"])
@login_required
@perm_accounts.require(http_exception=401)
def account_edit():
    
    acc_id = int(request.form['account_id'])
    acc_name = request.form['account_name']
    acc_pw = request.form['account_pw']
    
    note = request.form['change_note'].strip()
    
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
        
    # if there are roles, add new ones, remove the ones that aren't there
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
            new_db_roles = db.session.query(Role).filter(or_(Role.name == name for name in roles_new))
            for role in new_db_roles:
                acc.roles.append(role)
        
        sendRolesChanged(account_edit, acc.id, current_user.id, [x for x in roles_new], [x.name for x in roles_to_remove], note)
    else:
        # make sure all roles are removed
        roles_to_remove = []
        for role in acc.roles:
            roles_to_remove.append(role)
        
        for role in roles_to_remove:
            acc.roles.remove(role)
        db.session.flush()
        
        sendRolesChanged(account_edit, acc.id, current_user.id, [x.name for x in roles_to_remove], [], note)

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
            if acc.current_char != char_id:
                # remove all the access tokens
                acc.ssoToken = None
                acc.current_char = char_id
    
    db.session.commit()
    return redirect(url_for('.account_self'), code=303)

@bp_settings.route("/account_self", methods=["GET"])
@login_required
@perm_settings.require(http_exception=401)
def account_self():
    acc = db.session.query(Account).filter(Account.id == current_user.id).first()
    return render_template("settings/self.html", account=acc)

@bp_settings.route("/api/account/disabled", methods=['POST'])
@login_required
@perm_accounts.require(http_exception=401)
def account_disabled():
    accid = int(request.form['id'])
    acc = db.session.query(Account).filter(Account.id == accid).first()
    status = request.form['disabled']
    logger.info("%s sets account %s to %s", current_user.username, acc.username, status)
    if status == 'false':
        status = False
    else:
        status = True
    
    acc.disabled = status
    db.session.commit()
    return "OK"

@bp_settings.route("/bans", methods=["GET"])
@login_required
@perm_bans.require(http_exception=401)
def bans():
    bans = db.session.query(Ban).order_by(asc(Ban.name)).all()
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
    
    return redirect(url_for(".bans"))

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

    return redirect(url_for(".bans"))

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
    
    return redirect(url_for(".bans"))

@bp_settings.route("/api/account/<int:acc_id>", methods=["DELETE"])
@login_required
@perm_admin.require(http_exception=401)
def api_account_delete(acc_id):
    db.session.query(Account).filter(Account.id == acc_id).delete();
    db.session.commit();
    return flask.jsonify(status="OK")

@bp_settings.route("/fleet/status/set/<int:gid>", methods=["POST"])
@login_required
@perm_management.require(http_exception=401)
def fleet_status_set(gid):
    action = request.form['action']
    group = db.session.query(WaitlistGroup).get(gid)
    if action == "status":
        text = request.form['status']
        xup = request.form.get('xup', 'off')
        influence = request.form.get('influence')
        influence = False if influence is None else True
        xup_text = "closed"
        if xup == 'off':
            xup = False
        else:
            xup = True
            xup_text = "open"
 
        if xup != group.enabled:
            group.enabled = xup
            logger.info("XUP was set to %s by %s", xup, current_user.username)
        
        if influence != group.influence:
            group.influence = influence
            logger.info("Influence setting of grp %s was changed to %s by %s", group.groupID, influence, current_user.username)
        
        if perm_leadership.can() or perm_officer.can():
            group.status = text
            logger.info("Status was set to %s by %s", group.status, current_user.username)
            flash("Status was set to "+text+", xup is "+xup_text, "success")
             
        else:
            if text == "Running" or text == "Down" or text == "Forming":
                group.status = text
                logger.info("Status was set to %s by %s", group.status, current_user.username)
                flash("Status was set to "+text+", xup is "+xup_text, "success")
            else:
                logger.info("%s tried to set the status to %s and did not have the rights", current_user.username, group.status)
                flash("You do not have the rights to change the status to "+text, "danger")
                flash("XUP is now "+xup_text, "success")
    elif action == "fc":
        group.fcs.append(current_user)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} sets them self as FC\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), current_user.username))

        flash("You added your self to FCs "+current_user.get_eve_name(), "success")
    elif action == "manager":
        group.manager.append(current_user)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} sets them self as Fleet Manager\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), current_user.username))

        flash("You added your self to manager "+current_user.get_eve_name(), "success")
    elif action == "manager-remove":
        accountID = int(request.form['accountID'])
        account = db.session.query(Account).get(accountID)
    
        with open("set_history.log", "a+") as f:
            f.write('{} - {} is removed as Fleet Manager by {}\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), account.username, current_user.username))

        try:
            group.manager.remove(account)
        except ValueError:
            pass
    elif action == "fc-remove":
        accountID = int(request.form['accountID'])
        account = db.session.query(Account).get(accountID)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} is removed as FC by {}\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), account.username, current_user.username))

        try:
            group.fcs.remove(account)
        except ValueError:
            pass
    elif action == "add-backseat":
        group.backseats.append(current_user)

        with open("set_history.log", "a+") as f:
            f.write('{} - {} sets them self as Backseat\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), current_user.username))

        flash("You added your self as Backseat "+current_user.get_eve_name(), "success")
    elif action == "remove-backseat":
        accountID = int(request.form['accountID'])
        account = db.session.query(Account).get(accountID)
        with open("set_history.log", "a+") as f:
            f.write('{} - {} is removed as Backseat by {}\n'.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), account.username, current_user.username))
        
        try:
            group.backseats.remove(account)
        except ValueError:
            pass
    
    db.session.commit()
    
    event = StatusChangedSSE(group)
    sendServerSentEvent(event)
    
    return redirect(url_for(".fleet"), code=303)

@bp_settings.route("/fleet/location/set/<int:gid>", methods=["POST"])
@login_required
@perm_fleetlocation.require(http_exception=401)
def fleet_location_set(gid):
    group = db.session.query(WaitlistGroup).get(gid)
    action = request.form['action']
    if action == "constellation":
        name = request.form['name']
        constellation = get_constellation(name)
        if constellation is None:
            flash("This constellation does not exist! "+name)
            return redirect(url_for(".fleet"), code=303)
        
        # if we set the constellation look up if we already know dock and hq system
        inc_layout = db.session.query(IncursionLayout).filter(IncursionLayout.constellation == constellation.constellationID).first()

        if group.groupName == "default": # if default waitlist, set all of them
            groups = db.session.query(WaitlistGroup).all()
            logger.info("All Constellations were set to %s by %s", name, current_user.username)
            for group in groups:
                group.constellation = constellation

                # if we know it, set the other information
                if inc_layout is not None:
                    group.system = inc_layout.obj_headquarter
                    logger.info("%s System was autoset to %s by %s for %s", group.groupName, group.system.solarSystemName, current_user.username, group.groupName)
                    group.dockup = inc_layout.obj_dockup
                    logger.info("%s Dock was autoset to %s by %s for %s", group.groupName, group.dockup.stationName, current_user.username, group.groupName)
                else:
                    flash("No Constellation Layout Data found!")
                    group.system = None
                    group.dockup = None
                          
            flash("All Constellations were set to " + name + "!", "success")
        else: # if not default waitlist set only the single waitlist
            group.constellation = constellation
            logger.info("%s Constellation was set to %s by %s", group.groupName, name, current_user.username)
            # if we set the constellation look up if we already know dock and hq system
            inc_layout = db.session.query(IncursionLayout).filter(IncursionLayout.constellation == group.constellation.constellationID).first()
            # if we know it, set the other information
            if inc_layout is not None:
                group.system = inc_layout.obj_headquarter
                logger.info("%s System was autoset to %s by %s", group.groupName, group.system.solarSystemName, current_user.username)
                group.dockup = inc_layout.obj_dockup
                logger.info("%s Dock was autoset to %s by %s", group.groupName, group.dockup.stationName, current_user.username)
            else:
                flash("No Constellation Layout Data found!")
                group.system = None
                group.dockup = None
                      
            flash(group.displayName + " Constellation was set to " + name, "success")
    elif action == "system":
        name = request.form['name']
        system = get_system(name)
        if system == None:
            flash("Invalid system name "+name, "danger")
            return redirect(url_for(".fleet"), code=303)
        
        if group.groupName == "default":
            groups = db.session.query(WaitlistGroup).all()
            for group in groups:
                group.system = system
            
            logger.info("All Systems were set to %s by %s", name, current_user.username, group.groupName)
            flash("All Systems were set to "+name, "success")
        else:
            group.system = system
            logger.info(group.displayName + " System was set to %s by %s", name, current_user.username)
            flash(group.displayName + " System was set to "+name, "success")
    elif action == "dock":
        name = request.form['name']
        station = get_station(name);
        if station == None:
            flash("Invalid station name "+name, "danger")
            return redirect(url_for(".fleet"), code=303)
        if group.displayName == "default":
            groups = db.session.query(WaitlistGroup).all()
            station = get_station(name)
            for group in groups:
                group.dockup = station
            
            logger.info("All Docks were set to %s by %s", name, current_user.username)
            flash("All Dock were set to " + name, "success")
        else:
            group.dockup = get_station(name)
            logger.info("%s Dock was set to %s by %s", group.displayName, name, current_user.username)
            flash(group.displayName + " Dock was set to " + name, "success")
    
    db.session.commit()

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
        flash("Type IDs were updated!", "success")
    
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
        flash("Constellations and Systems were updated!", "success")
    
    return redirect(url_for('.sde_settings'))

@bp_settings.route("/sde/update/stations", methods=["POST"])
@login_required
@perm_dev.require(http_exception=401)
def update_stations():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "yaml"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if (path.isfile(dest_name)):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        sde.update_stations(dest_name)
        flash("Stations were updated!", "success")
    
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
        flash("Layouts were updated!", "success")
    
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
        if (path.isfile(dest_name)):
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

@bp_settings.route("/whitelist", methods=["GET"])
@login_required
@perm_bans.require(http_exception=401)
def whitelist():
    whitelistings = db.session.query(Whitelist).join(Character, (Whitelist.characterID == Character.id)).order_by(asc(Character.eve_name)).all()
    return render_template("settings/whitelist.html", wl=whitelistings)

@bp_settings.route("/whitelist_change", methods=["POST"])
@login_required
@perm_leadership.require(http_exception=401)
def whitelist_change():
    action = request.form['change'] # whitelist, unwhitelist
    target = request.form['target'] # name of target
    if action == "whitelist":
        reason = request.form['reason'] # reason for whitelist
    
    targets = target.split("\n")

    # pre-cache names for a faster api to not hit request limit
    names_to_cache = []
    for line in targets:
        line = line.strip()
        wl_name, _, wl_admin = get_info_from_ban(line)
        names_to_cache.append(wl_name)
        if wl_admin is not None:
            names_to_cache.append(wl_admin)
    
    eve_api_cache_char_ids(names_to_cache)
    
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
    
    if wl_reason == None or not leadership:
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

    #check if ban already there
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
    action = request.form['change'] # whitelist, unwhitelist
    target = request.form['target'] # name of target

    target = target.strip()
    
    
    if action == "whitelist":
        reason = request.form['reason'] # reason for ban
        whitelist_by_name(target, perm_leadership.can(), reason)
    elif action == "unwhitelist":
        unwhitelist_by_name(target)

    return redirect(url_for(".withelist"))

@bp_settings.route("/whitelist_unlist", methods=["POST"])
@login_required
@perm_bans.require(http_exception=401)
def whitelist_unlist():
    target = request.form['target'] # name of target
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
    
    return render_template("/settings/ts.html", active=active_ts_setting, all=all_ts_settings)

@bp_settings.route("/ts", methods=["POST"])
@login_required
@perm_management.require()
def teamspeak_change():
    action = request.form['action'] # add/remove, set
    if action == "add" and perm_leadership.can():
        displayName = request.form['displayName']
        host = request.form['internalHost']
        port = int(request.form['internalPort'])
        displayHost = request.form['displayHost']
        displayPort = int(request.form['displayPort'])
        queryName = request.form['queryName']
        queryPassword = request.form['queryPassword']
        serverID = int(request.form['serverID'])
        channelID = int(request.form['channelID'])
        clientName = request.form['clientName']
        safetyChannelID = request.form['safetyChannelID']
        ts = TeamspeakDatum(
                            displayName=displayName,
                            host=host,
                            port=port,
                            displayHost=displayHost,
                            displayPort=displayPort,
                            queryName=queryName,
                            queryPassword=queryPassword,
                            serverID=serverID,
                            channelID=channelID,
                            clientName=clientName,
                            safetyChannelID=safetyChannelID
                            )
        db.session.add(ts)
        db.session.commit()
    elif action == "remove" and perm_leadership.can():
        teamspeakID = int(request.form['teamspeakID'])
        db.session.query(TeamspeakDatum).filter(TeamspeakDatum.teamspeakID == teamspeakID).delete()
        active_id = sget_active_ts_id()
        if active_id is not None and active_id == teamspeakID:
            sset_active_ts_id(None)
            change_connection()
        db.session.commit()
    elif action == "set":
        teamspeakID = int(request.form['teamspeakID'])
        active_id = sget_active_ts_id()
        sset_active_ts_id(teamspeakID)
        if active_id is None or active_id != teamspeakID:
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

    accounts = db.session.query(Account).options(joinedload('characters')).join(Account.roles).filter(((Role.name == WTMRoles.fc) | (Role.name == WTMRoles.lm)) & (Account.disabled == False)).order_by(Account.username).all()

    response = Response(iter_accs(accounts), mimetype='text/csv')
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