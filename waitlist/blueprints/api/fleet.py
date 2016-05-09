from flask.blueprints import Blueprint
import logging
from waitlist.data.perm import perm_management
from flask_login import login_required, current_user
from waitlist.storage.database import CrestFleet
from waitlist import db
import flask
bp = Blueprint('api_fleet', __name__)
logger = logging.getLogger(__name__)

@bp.route("/<int:fleetID>/", methods=["DELETE"])
@login_required
@perm_management.require(http_exception=401)
def removeFleet(fleetID):
    logger.info("%s deletes crest fleet %i", current_user.username, fleetID)
    db.session.query(CrestFleet).filter(CrestFleet.fleetID == fleetID).delete()
    db.session.commit()
    return flask.jsonify(status_code=200, message="Fleet Deleted")