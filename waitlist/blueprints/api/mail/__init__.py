import logging
from flask.blueprints import Blueprint
from flask_login import login_required, current_user
from flask.globals import request
import flask

from waitlist.sso import add_token
from waitlist.utility.swagger import esi_scopes
from waitlist.utility.swagger.eve import make_error_response, ESIResponse
from waitlist.utility.swagger.evemail import send_mail
from flask.helpers import make_response, url_for
import json
from waitlist.permissions import perm_manager
from werkzeug.utils import redirect
from waitlist.blueprints.fc_sso import add_sso_handler, get_sso_redirect
from waitlist.storage.database import Account, AccountNote, SSOToken
from sqlalchemy import or_
from waitlist import db
from waitlist.utility.constants import account_notes
from waitlist.signal.handler import account
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

    token: SSOToken = current_user.get_a_sso_token_with_scopes(esi_scopes.mail_scopes)

    if token is None:
        return flask.abort(412, 'Not Authenticated for esi-mail.send_mail.v1')

    body = request.form.get('mailBody')
    subject = request.form.get('mailSubject')
    recipients = json.loads(request.form.get('mailRecipients'))
    target_chars = []
    for rec in recipients:
        if rec['recipient_type'] == 'character':
            target_chars.append(rec['recipient_id'])
    target_accs = db.session.query(Account).filter(
            or_(Account.current_char == charid for charid in target_chars)).all()

    resp = send_mail(token, recipients, body, subject)
    if resp.status == 201:
        history_entry: AccountNote = AccountNote(
            accountID=current_user.id,
            byAccountID=current_user.id,
            type=account_notes.TYPE_SENT_ACCOUNT_MAIL)
        history_entry.jsonPayload = {
            'sender_character_id': current_user.get_eve_id(),
            'recipients': recipients,
            'body': body,
            'subject': subject
        }
        db.session.add(history_entry)
        for acc in target_accs:
            acc.had_welcome_mail = True
            history_entry = AccountNote(accountID=acc.id,
                                        byAccountID=current_user.id,
                                        type=account_notes.
                                        TYPE_GOT_ACCOUNT_MAIL)
            history_entry.jsonPayload = {
                'sender_character_id': current_user.get_eve_id(),
                'target_character_id': acc.current_char,
                'mail_body': body,
                'subject': subject
            }
            db.session.add(history_entry)
        db.session.commit()
    else:
        esi_resp: ESIResponse = make_error_response(resp)
        if esi_resp.is_monolith_error():
            return make_response(esi_resp.get_monolith_error()['error_label'], resp.status)

    return make_response(str(resp.data) if resp.data is not None else '', resp.status)


def handle_mail_sso_cb(tokens):
    add_token(tokens)
    return redirect(url_for('accounts.accounts'))


@bp.route('/auth', methods=['GET'])
@login_required
@perm_manager.require('send_mail')
def auth():
    return get_sso_redirect('mail', 'esi-mail.send_mail.v1')


add_sso_handler('mail', handle_mail_sso_cb)

