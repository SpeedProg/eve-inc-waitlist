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
from waitlist.blueprints.fleet import handle_token_update
from waitlist.permissions import perm_manager
from waitlist.utility.swagger.evemail import open_mail

bp = Blueprint('api_ui', __name__)
logger = logging.getLogger(__name__)


@bp.route('/openwindow/newmail', methods=['POST'])
@login_required
@perm_manager.require('commandcore')
def post_esi_openwindow_newmail():
    needs_refresh = True
    if current_user.ssoToken is not None:
        for scope in current_user.ssoToken.scopes:
            if scope.scopeName == 'esi-ui.open_window.v1':
                needs_refresh = False

    if needs_refresh:
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
        elif rec['receipient_type'] == 'mailing_list':
            if mailinglist_id is not None or alliance_or_corp is not None:
                raise ValueError("Only one alliance or corp or mailing list at maximum can be receipient of a mail")
            mailinglist_id = rec['recipient_id']

    response = open_mail(receipients, body, subject, alliance_or_corp, mailinglist_id)
    if response.is_error():
        flask.abort(response.error(), response.code())

    return make_response('', response.code())


def handle_sso_cb(tokens):
    handle_token_update(tokens)
    return redirect(url_for('feedback.settings'))


@bp.route('/auth', methods=['GET'])
@login_required
@perm_manager.require('commandcore')
def auth():
    return get_sso_redirect('esi_ui', 'esi-ui.open_window.v1')

add_sso_handler('esi_ui', handle_sso_cb)
