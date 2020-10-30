
from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from flask import jsonify

from waitlist.utility.coms import get_connector

bp = Blueprint('api_ts3', __name__)
logger = logging.getLogger(__name__)


@bp.route("/test_poke")
@login_required
def test_poke():
    com_connector = get_connector()
    if com_connector is not None:
        com_connector.send_notification(current_user.get_eve_name(), 'Test Poke')
    resp = jsonify(status_code=201, message='Poke was send!')
    resp.status_code = 201
    return resp

