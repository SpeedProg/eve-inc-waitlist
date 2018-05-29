import logging
from typing import List

import flask
from flask import Blueprint
from flask import json
from flask import make_response
from flask import redirect
from flask import url_for
from flask.globals import request
from flask_login import login_required, current_user

from waitlist.blueprints.fc_sso import get_sso_redirect, add_sso_handler
from waitlist.permissions import perm_manager
from waitlist.sso import add_token
from waitlist.storage.database import SSOToken
from waitlist.utility.swagger import esi_scopes
from waitlist.utility.swagger.evemail import open_mail

bp = Blueprint('api_ui', __name__)
logger = logging.getLogger(__name__)


@bp.route('/openwindow/newmail', methods=['POST'])
@login_required
@perm_manager.require('commandcore')
def post_esi_openwindow_newmail():
    token: SSOToken = current_user.get_a_sso_token_with_scopes(esi_scopes.open_ui_window)

    if token is None:
        return flask.abort(412, 'Not Authenticated for esi-ui.open_window.v1')

    recipients_str: str = request.form['mailRecipients']

    subject: str = request.form['mailSubject']
    body: str = request.form['mailBody']

    recipients_json = json.loads(recipients_str)

    receipients: List[int] = []

    alliance_or_corp: int = None
    mailinglist_id: int = None

    for rec in recipients_json:
        if rec['recipient_type'] == 'character':
            receipients.append(rec['recipient_id'])
        elif rec['recipient_type'] == 'alliance' or rec['recipient_type'] == 'corporation':
            if alliance_or_corp is not None or mailinglist_id is not None:
                raise ValueError("Only one alliance or corp or mailing list at maximum can be receipient of a mail")
            alliance_or_corp = rec['recipient_id']
        elif rec['recipient_type'] == 'mailing_list':
            if mailinglist_id is not None or alliance_or_corp is not None:
                raise ValueError("Only one alliance or corp or mailing list at maximum can be receipient of a mail")
            mailinglist_id = rec['recipient_id']

    response = open_mail(token, receipients, body, subject, alliance_or_corp, mailinglist_id)
    if response.is_error():
        flask.abort(response.error(), response.code())

    return make_response('OK', response.code())


def handle_open_ui_sso_cb(tokens):
    add_token(tokens)
    return redirect(url_for('feedback.settings'))


@bp.route('/auth', methods=['GET'])
@login_required
@perm_manager.require('commandcore')
def auth():
    return get_sso_redirect('esi_ui', 'esi-ui.open_window.v1')


add_sso_handler('esi_ui', handle_open_ui_sso_cb)
