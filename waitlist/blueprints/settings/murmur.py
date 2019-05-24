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
from waitlist.storage.database import MurmurDatum
from waitlist.utility.settings import sget_active_coms_id,\
    sget_active_coms_type, sset_active_coms_id, sset_active_coms_type
from waitlist.utility.config import disable_murmur
from waitlist.utility.murmur.connector import MurmurConnector
from waitlist.utility.coms import get_connector, set_connector
from flask_babel import gettext, lazy_gettext


bp = Blueprint('murmur', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('murmur_change')
perm_manager.define_permission('murmur_view')
perm_manager.define_permission('murmur_edit')

perm_change_server = perm_manager.get_permission('murmur_change')\
    .union(perm_manager.get_permission('murmur_edit'))
perm_view_server = perm_change_server
perm_edit_server = perm_manager.get_permission('murmur_edit')


@bp.route("/murmur", methods=["GET"])
@login_required
@perm_view_server.require()
def murmur():
    active_coms_type = sget_active_coms_type()
    active_coms_id = sget_active_coms_id()
    active_murmur_setting = None
    if active_coms_type == 'murmur' and active_coms_id is not None:
        active_murmur_setting = db.session.query(MurmurDatum).get(active_coms_id)

    all_murmur_settings = db.session.query(MurmurDatum).all()

    return render_template("settings/murmur.html", active=active_murmur_setting, all=all_murmur_settings)


@bp.route("/murmur", methods=["POST"])
@login_required
@perm_change_server.require()
def murmur_change():
    action = request.form['action']  # add/remove, set
    if action == "add" and perm_edit_server.can():
        display_name = request.form['displayName']
        host = request.form['internalHost']
        port = int(request.form['internalPort'])
        display_host = request.form['displayHost']
        display_port = int(request.form['displayPort'])
        server_id = int(request.form['serverID'])
        safety_channel_id = request.form['safetyChannelID']
        datum = MurmurDatum(
            displayName=display_name,
            grpcHost=host,
            grpcPort=port,
            displayHost=display_host,
            displayPort=display_port,
            serverID=server_id,
            safetyChannelID=safety_channel_id
        )
        db.session.add(datum)
        db.session.commit()
        # set as active ts if there was none before
        active_coms_type = sget_active_coms_type()
        if active_coms_type is None:
            sset_active_coms_type('murmur')
        if active_coms_type is None or sget_active_coms_id() is None:
            sset_active_coms_id(datum.murmurID)
            com_connector = get_connector()
            if com_connector is not None:
                com_connector.close()
            com_connector = MurmurConnector()
            set_connector(com_connector)
    elif action == "remove" and perm_edit_server.can():
        murmur_id = int(request.form['murmurID'])
        db.session.query(MurmurDatum).filter(MurmurDatum.murmurID == murmur_id).delete()
        active_id = sget_active_coms_id()
        active_type = sget_active_coms_type()
        if active_type == 'murmur' and active_id == murmur_id:
            sset_active_coms_type(None)
            sset_active_coms_id(None)
            com_connector = get_connector()
            com_connector.close()
            set_connector(None)
        db.session.commit()
    elif action == "set":
        murmur_id = int(request.form['murmurID'])
        active_type = sget_active_coms_type()
        active_id = sget_active_coms_id()
        com_connector = get_connector()
        if com_connector is not None:
            com_connector.close()
        com_connector = MurmurConnector()
        set_connector(com_connector)
        sset_active_coms_id(murmur_id)
        sset_active_coms_type('murmur')
    else:
        flask.abort(400)

    return redirect(url_for("murmur.murmur"))

if not disable_murmur:
    add_menu_entry('murmur.murmur', lazy_gettext('Murmur Settings'), perm_view_server.can)
