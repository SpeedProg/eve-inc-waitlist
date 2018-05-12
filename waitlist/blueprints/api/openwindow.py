from esipy.exceptions import APIException
from flask.blueprints import Blueprint
import logging
from flask.globals import request
from flask.helpers import make_response

from waitlist.permissions import perm_manager
from waitlist.utility.swagger.character_info import open_information
from flask_login import login_required

bp = Blueprint('api_eve_openwindow', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('fleet_management')

perm_fleet_manage = perm_manager.get_permission('fleet_management')


# /characters/<characterID>/ui/openwindow/ownerdetails/
@bp.route('/ownerdetails/', methods=['POST'])
@login_required
@perm_fleet_manage.require()
def ownerdetails():
    eve_id = int(request.form.get("characterID"))

    try:
        resp = open_information(eve_id)
        return make_response(resp.error() if resp.is_error() else '', resp.code())
    except APIException as e:
        return make_response(f"Got APIException while opening ownerdetails for {eve_id}", 500)

