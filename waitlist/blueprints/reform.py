from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from flask.templating import render_template

from waitlist.permissions import perm_manager

bp = Blueprint('fleet_reform', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('fleet_management')

perm_fleet_manage = perm_manager.get_permission('fleet_management')


@bp.route("/")
@login_required
@perm_fleet_manage.require()
def index():
    return render_template("fleet/reform/index.html")
