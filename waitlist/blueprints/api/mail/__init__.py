import logging
from flask.blueprints import Blueprint
from flask_login import login_required, current_user
from flask.globals import request
import flask
from waitlist.utility.swagger.evemail import send_mail
from flask.helpers import make_response, url_for
import json
from waitlist.permissions import perm_manager
from waitlist.blueprints.fleet import handle_token_update
from werkzeug.utils import redirect
from waitlist.blueprints.fc_sso import add_sso_handler, get_sso_redirect
from waitlist.storage.database import Account, AccountNote
from sqlalchemy import or_
from waitlist import db
bp = Blueprint('api_mail', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('send_mail')

@bp.route('/', methods=['POST'])
@login_required
@perm_manager.require('send_mail')
def send_esi_mail():
    """
    mailRecipients => JSON String recipients=[{"recipient_id": 0, "recipient_type": "character|alliance"}]
    mailBody => String
    mailSubject => String
    """
    needs_refresh = True
    if current_user.ssoToken is not None:
        for scope in current_user.ssoToken.scopes:
            if scope.scopeName == 'esi-mail.send_mail.v1':
                needs_refresh = False
    
    if needs_refresh:
        return flask.abort(412, 'Not Authenticated for esi-mail.send_mail.v1')
    
    body = request.form.get('mailBody')
    subject = request.form.get('mailSubject')
    recipients = json.loads(request.form.get('mailRecipients'))
    target_chars = []
    for rec in recipients:
        if rec['recipient_type'] == 'character':
            target_chars.append(rec['recipient_id'])
    
    resp = send_mail(recipients, body, subject)
    if resp.status == 201:
        target_accs = db.session.query(Account).filter(
            or_(Account.current_char == charid for charid in target_chars)).all()
        for acc in target_accs:
            acc.had_welcome_mail = True
            history_entry = AccountNote(accountID=acc.id, byAccountID=current_user.id,
                                        note="Send mail to main character linked to this account with id="
                                             + str(acc.current_char) + " and name="
                                             + acc.current_char_obj.eve_name)
            db.session.add(history_entry)
        db.session.commit()

    return make_response(str(resp.data) if resp.data is not None else '', resp.status)


def handle_sso_cb(tokens):
    handle_token_update(tokens)
    return redirect(url_for('accounts.accounts'))


@bp.route('/auth', methods=['GET'])
@login_required
@perm_manager.require('send_mail')
def auth():
    return get_sso_redirect('mail', 'esi-mail.send_mail.v1')


add_sso_handler('mail', handle_sso_cb)

