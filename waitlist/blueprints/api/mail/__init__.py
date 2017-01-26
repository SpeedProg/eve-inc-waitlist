import logging
from flask.blueprints import Blueprint
from flask_login import login_required, current_user
from waitlist.data.perm import perm_management, perm_leadership
from flask.globals import request
import flask
from waitlist.utility.swagger.evemail import sendMail
from flask.helpers import make_response, url_for
import json
from waitlist.permissions import perm_manager
from waitlist.blueprints.fleet import handle_token_update
from werkzeug.utils import redirect
from waitlist.blueprints.fc_sso import add_sso_handler, get_sso_redirect
from datetime import date, datetime, timedelta
bp = Blueprint('api_mail', __name__)
logger = logging.getLogger(__name__)

@bp.route('/', methods=['POST'])
@login_required
@perm_manager.require('send_mail')
def send_esi_mail():
    '''
    mailRecipients => JSON String recipients=[{"recipient_id": 0, "recipient_type": "character|alliance"}]
    mailBody => String
    mailSubject => String
    '''
    needsRefresh = True
    if current_user.ssoToken != None:
        for scope in current_user.ssoToken.scopes:
            if scope.scopeName == 'esi-mail.send_mail.v1':
                needsRefresh = False
    
    if needsRefresh:
        return flask.abort(412, 'Not Authenticated for esi-mail.send_mail.v1')
    
    body = request.form.get('mailBody')
    subject = request.form.get('mailSubject')
    recipients = json.loads(request.form.get('mailRecipients'))
    resp = sendMail(recipients, body, subject)
    return make_response(str(resp.data) if resp.data is not None else '', resp.status)

def handle_sso_cb(tokens):
    handle_token_update(tokens)
    return redirect(url_for('settings.accounts'))

@bp.route('/auth', methods=['GET'])
@login_required
@perm_manager.require('send_mail')
def auth():
    return get_sso_redirect('mail', 'esi-mail.send_mail.v1')

add_sso_handler('mail', handle_sso_cb)
