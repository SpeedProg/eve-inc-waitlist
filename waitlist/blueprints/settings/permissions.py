import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from flask import Blueprint
from flask import render_template
from flask_login import login_required

from waitlist.permissions import perm_manager
from waitlist.permissions.manager import StaticRoles

bp = Blueprint('settings_permissions', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission(StaticRoles.ADMIN)
perm = perm_manager.get_permission(StaticRoles.ADMIN)

@bp.route("/")
@login_required
@perm.require(http_exception=401)
def view_permissions():
    return render_template('settings/permissions/config.html')