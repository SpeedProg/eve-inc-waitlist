import logging

from flask import Blueprint
from flask import Response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required, current_user

from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager
from waitlist.permissions.manager import StaticPermissions
from waitlist.signal.signals import send_roles_added

bp = Blueprint('settings_permissions', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission(StaticPermissions.ADMIN)


@bp.route("/", methods=['GET'])
@login_required
@perm_manager.require(StaticPermissions.ADMIN)
def view_permissions() -> Response:
    return render_template('settings/permissions/config.html')


@bp.route("/add_role", methods=['POST'])
@login_required
@perm_manager.require(StaticPermissions.ADMIN)
def add_role() -> Response:
    role_name: str = request.form['role_name']
    role_display_name: str = request.form['role_display_name']

    perm_manager.add_role(role_name, role_display_name)
    send_roles_added(add_role, current_user.id, role_name, role_display_name)

    return redirect(url_for('.view_permissions'), code=303)

add_menu_entry('settings_permissions.view_permissions', 'Permissions',
               lambda: perm_manager.get_permission(StaticPermissions.ADMIN).can())
