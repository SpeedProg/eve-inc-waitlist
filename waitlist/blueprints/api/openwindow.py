from __future__ import absolute_import
from flask.blueprints import Blueprint
import logging
from waitlist.data.perm import perm_management
from flask.globals import request
from flask.helpers import make_response
from waitlist.utility.swagger.character_info import open_information
from flask_login import login_required
bp = Blueprint('api_eve_openwindow', __name__)
logger = logging.getLogger(__name__)

#/characters/<characterID>/ui/openwindow/ownerdetails/
@bp.route('/ownerdetails/', methods=['POST'])
@login_required
@perm_management.require()
def ownerdetails():
    eveId = int(request.form.get("characterID"))

    resp = open_information(eveId)
    return make_response(resp.error() if resp.is_error() else '', resp.code())