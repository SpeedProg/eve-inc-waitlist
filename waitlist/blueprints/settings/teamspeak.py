import logging

import flask
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required

from waitlist.base import db
from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager
from waitlist.storage.database import TeamspeakDatum
from waitlist.utility.settings import sget_active_coms_id,\
    sget_active_coms_type, sset_active_coms_id, sset_active_coms_type
from waitlist.utility.config import disable_teamspeak
from waitlist.utility.coms import get_connector, set_connector
from waitlist.ts3.connection import TS3Connector

from flask_babel import gettext, lazy_gettext


bp = Blueprint('teamspeak', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('teamspeak_change')
perm_manager.define_permission('teamspeak_view')
perm_manager.define_permission('teamspeak_edit')

perm_change_server = perm_manager.get_permission('teamspeak_change')\
    .union(perm_manager.get_permission('teamspeak_edit'))
perm_view_server = perm_change_server
perm_edit_server = perm_manager.get_permission('teamspeak_edit')


@bp.route("/ts", methods=["GET"])
@login_required
@perm_view_server.require()
def teamspeak():
    active_coms_type = sget_active_coms_type()
    active_coms_id = sget_active_coms_id()

    active_ts_setting = None
    if active_coms_type == 'ts3' and active_coms_id is not None:
        active_ts_setting = db.session.query(TeamspeakDatum).get(active_coms_id)

    all_ts_settings = db.session.query(TeamspeakDatum).all()

    return render_template("settings/ts.html", active=active_ts_setting, all=all_ts_settings)


@bp.route("/ts", methods=["POST"])
@login_required
@perm_change_server.require()
def teamspeak_change():
    action = request.form['action']  # add/remove, set
    if action == "add" and perm_edit_server.can():
        display_name = request.form['displayName']
        host = request.form['internalHost']
        port = int(request.form['internalPort'])
        display_host = request.form['displayHost']
        display_port = int(request.form['displayPort'])
        query_name = request.form['queryName']
        query_password = request.form['queryPassword']
        server_id = int(request.form['serverID'])
        channel_id = int(request.form['channelID'])
        client_name = request.form['clientName']
        safety_channel_id = request.form['safetyChannelID']
        ts = TeamspeakDatum(
            displayName=display_name,
            host=host,
            port=port,
            displayHost=display_host,
            displayPort=display_port,
            queryName=query_name,
            queryPassword=query_password,
            serverID=server_id,
            channelID=channel_id,
            clientName=client_name,
            safetyChannelID=safety_channel_id
        )
        db.session.add(ts)
        db.session.commit()
        # set as active ts if there was none before
        if sget_active_coms_id() is None:
            sset_active_coms_id(ts.teamspeakID)
            sset_active_coms_type('ts3')
            com_connector = get_connector()
            if com_connector is not None:
                com_connector.close()
                com_connector = TS3Connector()
                set_connector(com_connector)
    elif action == "remove" and perm_edit_server.can():
        teamspeak_id = int(request.form['teamspeakID'])
        db.session.query(TeamspeakDatum).filter(TeamspeakDatum.teamspeakID == teamspeak_id).delete()
        if sget_active_coms_type() == 'ts3':
            active_id = sget_active_coms_id()
            if active_id is not None and active_id == teamspeak_id:
                sset_active_coms_id(None)
                sset_active_coms_type(None)
                com_connector = get_connector()
                if com_connector is not None:
                    com_connector.close()
                    com_connector = None
                    set_connector(None)

        db.session.commit()
    elif action == "set":
        teamspeak_id = int(request.form['teamspeakID'])
        active_id = sget_active_coms_id()
        active_type = sget_active_coms_type()
        sset_active_coms_id(teamspeak_id)
        com_connector = get_connector()
        if active_type != 'ts3':
            sset_active_coms_type('ts3')
            if com_connector is not None:
                com_connector.close()
                com_connector = TS3Connector()
                set_connector(com_connector)
        else:
            if com_connector is None:
                com_connector = TS3Connector()
                set_connector(com_connector)
            else:
                com_connector.data_updated()

    else:
        flask.abort(400)

    return redirect(url_for("teamspeak.teamspeak"))

if not disable_teamspeak:
    add_menu_entry('teamspeak.teamspeak', lazy_gettext('TS Settings'), perm_view_server.can)
