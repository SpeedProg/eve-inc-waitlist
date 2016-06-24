from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from waitlist.data.perm import perm_management
from flask.templating import render_template

bp = Blueprint('fleet_reform', __name__)
logger = logging.getLogger(__name__)

@bp.route("/")
@login_required
@perm_management.require()
def index():
    return render_template("fleet/reform/index.html")