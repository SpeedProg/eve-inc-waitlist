import logging
import os

from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required
from os import path

from werkzeug.utils import secure_filename, redirect

from waitlist.blueprints.settings import add_menu_entry
from waitlist import app
from waitlist.permissions import perm_manager
from waitlist.utility import sde
from flask_babel import gettext, lazy_gettext

bp = Blueprint('sde', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('static_data_import')
perm_manager.define_permission('developer_tools')

perm_access = perm_manager.get_permission('static_data_import')
perm_developer = perm_manager.get_permission('developer_tools')


@bp.route("/sde/update/typeids", methods=["POST"])
@login_required
@perm_access.require(http_exception=401)
def update_type_ids():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "yaml"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if path.isfile(dest_name):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        sde.update_invtypes(dest_name)
        flash(gettext("Type IDs were updated!"), "success")

    return redirect(url_for('.sde_settings'))


@bp.route("/sde/update/map", methods=["POST"])
@login_required
@perm_access.require(http_exception=401)
def update_map():
    sde.update_constellations()
    flash(gettext("Constellations where updated!"), "success")
    sde.update_systems()
    flash(gettext("Systems were updated!"), "success")
    return redirect(url_for('.sde_settings'))


@bp.route("/sde/update/stations", methods=["POST"])
@login_required
@perm_access.require(http_exception=401)
def update_stations():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "yaml"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if path.isfile(dest_name):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        sde.update_stations(dest_name)
        flash(gettext("Stations were updated!"), "success")

    return redirect(url_for('.sde_settings'))


@bp.route("/sde/update/layouts", methods=["POST"])
@login_required
@perm_access.require(http_exception=401)
def update_layouts():
    f = request.files['file']
    if f and (f.filename.rsplit('.', 1)[1] == "bz2" or f.filename.rsplit('.', 1)[1] == "csv"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if path.isfile(dest_name):
            os.remove(dest_name)
        f.save(dest_name)
        # start the update
        sde.update_layouts(dest_name)
        flash(gettext("Layouts were updated!"), "success")

    return redirect(url_for('.sde_settings'))


@bp.route("/sde")
@login_required
@perm_access.require(http_exception=401)
def sde_settings():
    return render_template("settings/sde.html")


add_menu_entry('sde.sde_settings', lazy_gettext('Static Data Import'), perm_access.can)
