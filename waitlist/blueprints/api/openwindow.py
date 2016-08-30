from flask.blueprints import Blueprint
import logging
from pycrest.eve import AuthedConnectionB
from waitlist.utility.config import crest_client_id, crest_client_secret
from waitlist.data.perm import perm_management
from flask_login import login_required, current_user
from waitlist.utility.crest import create_token_cb
from flask.globals import request
from flask.helpers import make_response
bp = Blueprint('api_eve_openwindow', __name__)
logger = logging.getLogger(__name__)

@bp.route('/ownerdetails/', methods=['POST'])
@login_required
@perm_management.require()
def ownerdetails():
    eveId = int(request.form.get("characterID"))
    data = {
        'access_token': current_user.access_token,
        'refresh_token': current_user.refresh_token,
        'expires_in': current_user.access_token_expires
        }
    
    # get own character id
    con = AuthedConnectionB(data, "https://crest-tq.eveonline.com/", "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(current_user.id))
    authInfo = con.whoami()
    con._endpoint = "https://crest-tq.eveonline.com/characters/"+str(authInfo['CharacterID'])+"/"
    # send the request to eve api
    resp = con().ui.showOwnerDetails.post(json={'id': eveId})
    return make_response(resp.content, resp.status_code)