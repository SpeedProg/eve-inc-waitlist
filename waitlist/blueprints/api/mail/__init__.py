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
from waitlist.storage.database import linked_chars, Account, AccountNote
from sqlalchemy import or_
from waitlist.base import db
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
    target_chars = []
    for rec in recipients:
        if rec['recipient_type'] == 'character':
            target_chars.append(rec['recipient_id'])
    
    resp = sendMail(recipients, body, subject)
    if resp.status == 201:
        target_accs = db.session.query(Account).filter(or_(Account.current_char == charid for charid in target_chars)).all()
        for acc in target_accs:
            acc.had_welcome_mail = True
            historyEntry = AccountNote(accountID=acc.id, byAccountID=current_user.id, note="Send mail to main character linked to this account with id="+str(acc.current_char)+" and name="+acc.current_char_obj.eve_name)
            db.session.add(historyEntry)
        db.session.commit()

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

