import logging
from flask import Blueprint
from flask import render_template
from flask_login import login_required

from waitlist.base import db
from waitlist.permissions import perm_manager
from waitlist.storage.database import CrestFleet

bp = Blueprint('fleetview', __name__)
logger = logging.getLogger(__name__)


@bp.route("/")
@login_required
@perm_manager.require('fleetview')
def index():
    fleets = db.session.query(CrestFleet).filter((CrestFleet.comp is not None) & (CrestFleet.group is not None)).all()
    return render_template("settings/fleetspy/spy.html", fleets=fleets)
