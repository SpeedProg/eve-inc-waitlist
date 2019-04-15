import logging

from flask import Blueprint
from flask import Response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required, current_user

from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager, PermissionManager
from waitlist.permissions.manager import StaticPermissions
from waitlist.signal.signals import send_role_created, send_role_removed
from flask_babel import gettext, lazy_gettext
from flask.helpers import flash

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

    PermissionManager.add_role(role_name, role_display_name)
    send_role_created(add_role, current_user.id, role_name, role_display_name)

    return redirect(url_for('.view_permissions'), code=303)


add_menu_entry('settings_permissions.view_permissions', lazy_gettext('Permissions'),
               lambda: perm_manager.get_permission(StaticPermissions.ADMIN).can())

@bp.route("/remove_role", methods=['POST'])
@login_required
@perm_manager.require(StaticPermissions.ADMIN)
def remove_role() -> Response:
    role_id: int = int(request.form['role_id'])
    role: Role = PermissionManager.get_role(role_id)
    if role is None:
     flash(gettext('Role with id=%(role_id)d was not found, failed to delete',
                    role_id=role_id),
            "warning")
    else:
      role_display_name: str = role.displayName
      role_name: str = role.name

      if PermissionManager.remove_role(role_id):
          flash(
              gettext('Role with id=%(role_id)d was deleted',
                      role_id=role_id),
              "success")
          send_role_removed(remove_role, current_user.id, role_name,
                            role_display_name)
      else:
          flash(
              gettext('There was an unknown error deleting Role with id=%(role_id)d',
                      role_id=role_id),
              "warning")
    return redirect(url_for('.view_permissions'), code=303)


