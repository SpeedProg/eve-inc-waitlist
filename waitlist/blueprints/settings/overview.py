from flask import Blueprint, render_template
from flask_login import login_required
from flask_babel import lazy_gettext

from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager
from waitlist.utility.config import overview_show_count_for_approvals

bp = Blueprint('settings_overview', __name__)


perm_manager.define_permission('settings_access')

perm_access = perm_manager.get_permission('settings_access')

@bp.route("/")
@login_required
@perm_access.require(http_exception=401)
def overview():
   return render_template('settings/overview.html', show_count_for_approvals=overview_show_count_for_approvals)

add_menu_entry('settings_overview.overview', lazy_gettext('Overview'), lambda: True)

