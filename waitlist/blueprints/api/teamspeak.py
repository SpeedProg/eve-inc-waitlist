from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from waitlist.ts3.connection import send_poke
from flask import jsonify
bp = Blueprint('api_ts3', __name__)
logger = logging.getLogger(__name__)

@bp.route("/test_poke")
@login_required
def test_poke():
    send_poke(current_user.get_eve_name(), "Test Poke")
    resp = jsonify(status_code=201, message="Poke was send!")
    resp.status_code = 201
    return resp