import logging
import os
from bz2 import BZ2File

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
        flash("Type IDs were updated!", "success")

    return redirect(url_for('.sde_settings'))


@bp.route("/sde/update/map", methods=["POST"])
@login_required
@perm_access.require(http_exception=401)
def update_map():
    f = request.files['file']
    file_ext = f.filename.rsplit('.', 1)[1]
    if f and (file_ext == "bz2" or file_ext == "db"):
        filename = secure_filename(f.filename)
        dest_name = path.join(app.config['UPLOAD_FOLDER'], filename)
        if path.isfile(dest_name):
            os.remove(dest_name)
        f.save(dest_name)

        # if it is bz2 extract it
        if file_ext == "bz2":
            raw_file: str = dest_name.rsplit(".", 1)[0]
            with open(raw_file, 'wb') as new_file, BZ2File(dest_name, 'rb') as f:
                for data in iter(lambda: f.read(100 * 1024), b''):
                    new_file.write(data)
            dest_name = raw_file

        # start the update
        sde.update_constellations(dest_name)
        sde.update_systems(dest_name)
        flash("Constellations and Systems were updated!", "success")

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
        flash("Stations were updated!", "success")

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
        flash("Layouts were updated!", "success")

    return redirect(url_for('.sde_settings'))


@bp.route("/sde")
@login_required
@perm_access.require(http_exception=401)
def sde_settings():
    return render_template("settings/sde.html")

add_menu_entry('sde.sde_settings', 'Static Data Import', perm_access.can)
