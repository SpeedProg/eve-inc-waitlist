from flask import Response
from flask_login import login_required
from flask.templating import render_template

from waitlist.blueprints.settings import add_menu_entry
from waitlist.utility.settings import sget_insert, sset_insert
from flask.blueprints import Blueprint
import logging
from flask.globals import request
from flask.helpers import flash, url_for
from werkzeug.utils import redirect
from waitlist.permissions import perm_manager

bp = Blueprint('settings_inserts', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('inserts_edit')


@bp.route("/")
@login_required
@perm_manager.require('inserts_edit')
def index() -> Response:
    data = {'header': sget_insert('header')}
    return render_template("settings/inserts.html", inserts=data)


@bp.route("/change/<string:type_>", methods=["POST"])
@login_required
@perm_manager.require('inserts_edit')
def change(type_) -> Response:
    if type_ == "header":
        content = request.form.get('content')
        sset_insert('header', content)
        flash("Header Insert Saved")
    return redirect(url_for('settings_inserts.index'))


add_menu_entry('settings_inserts.index', 'Page Inserts', perm_manager.get_permission('inserts_edit').can)
