import logging

from flask import Blueprint, jsonify
from flask import abort
from flask import request
from flask_login import login_required

from waitlist.permissions import perm_manager
from waitlist.permissions.manager import StaticPermissions

bp = Blueprint('api_permission', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission(StaticPermissions.ADMIN)


@bp.route('/change', methods=['POST'])
@login_required
@perm_manager.require(StaticPermissions.ADMIN)
def change():
    perm_name: str = request.form.get('perm_name', None)
    role_name: str = request.form.get('role_name', None)
    perm_state_str: str = request.form.get('state', None)

    if perm_name is None or role_name is None or perm_state_str is None:
        abort(400, "A required parameter is missing or incorrect")
        return

    if not(perm_state_str == "true" or perm_state_str == "false"):
        abort(400, f"The state parameter contained an invalid value of [{perm_state_str}]")
        return

    perm_state = perm_state_str == "true"

    if perm_state:
        perm_manager.add_role_to_permission(perm_name, role_name)
    else:
        perm_manager.remove_role_from_permission(perm_name, role_name)

    # add a history entry

    return jsonify({'code': '200', 'msg': 'permission changed'})
