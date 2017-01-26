from __future__ import absolute_import
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

#/characters/<characterID>/ui/openwindow/ownerdetails/
@bp.route('/ownerdetails/', methods=['POST'])
@login_required
@perm_management.require()
def ownerdetails():
    eveId = int(request.form.get("characterID"))
    # TODO: if ssoToken == None or not right scope
    data = {
        'access_token': current_user.ssoToken.access_token,
        'refresh_token': current_user.ssoToken.refresh_token,
        'expires_in': current_user.ssoToken.access_token_expires
        }
    
    # get own character id
    con = AuthedConnectionB(data, "https://crest-tq.eveonline.com/", "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(current_user.id))
    authInfo = con.whoami()
    con._endpoint = "https://crest-tq.eveonline.com/characters/"+str(authInfo['CharacterID'])+"/"
    

    # send the request to eve api
    resp = con().ui.showOwnerDetails.post(json={'id': eveId})
    return make_response(resp.content, resp.status_code)

#/characters/<characterID>/ui/openwindow/newmail/
'''
body" : {
            "description" : "The contents of the body.",
            "isOptional" : false,
            "extraData" : null,
            "subContent" : null,
            "typePrettyName" : "Unicode string (unicode)",
            "type" : "String"
        },
        "corporationOrAllianceRecipient" : {
            "description" : "ID of your corporation or alliance. Mutually exlusive with mailing list mails.",
            "isOptional" : true,
            "extraData" : null,
            "subContent" : null,
            "typePrettyName" : "Long (64bit integer)",
            "type" : "Long"
        },
        "toMailingListId" : {
            "description" : "ID of a mailing list. Mutually exclusive with corporation or alliance mails.",
            "isOptional" : true,
            "extraData" : null,
            "subContent" : null,
            "typePrettyName" : "Long (64bit integer)",
            "type" : "Long"
        },
        "recipients" : {
            "description" : null,
            "isOptional" : true,
            "extraData" : "Dict",
            "subContent" : {
                "id" : {
                    "description" : "ID of character to address to. You can address at most 50 recipients.",
                    "isOptional" : false,
                    "extraData" : null,
                    "subContent" : null,
                    "typePrettyName" : "Long (64bit integer)",
                    "type" : "Long"
                }
            },
            "typePrettyName" : "Array of Dict",
            "type" : "Array"
        },
        "subject" : {
            "description" : "The contents of the subject field.",
            "isOptional" : false,
            "extraData" : null,
            "subContent" : null,
            "typePrettyName" : "Unicode string (unicode)",
            "type" : "String"
        }
'''
@bp.route('/newmail/', methods=['POST'])
@login_required
@perm_management.require()
def newmail():
    recipients = map(make_id_dict, request.form.get("mailRecipients").split(","))
    body = request.form.get('mailBody')
    subject = request.form.get('mailSubject')
    # TODO: check if token == None or not right scope
    data = {
        'access_token': current_user.ssoToken.access_token,
        'refresh_token': current_user.ssoToken.refresh_token,
        'expires_in': current_user.ssoToken.access_token_expires
        }
    
    # get own character id
    con = AuthedConnectionB(data, "https://crest-tq.eveonline.com/", "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(current_user.id))
    authInfo = con.whoami()
    con._endpoint = "https://crest-tq.eveonline.com/characters/"+str(authInfo['CharacterID'])+"/"
    #ui/showNewMailWindow/
    resp = con().ui.showNewMailWindow.post(json={
        'body': body,
        'subject': subject,
        'recipients': recipients
            }
        )
    return make_response(resp.content, resp.status_code)

def make_id_dict(_id):
    return {'id': int(_id)}