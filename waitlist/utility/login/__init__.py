import flask
import logging
from flask import current_app
from flask import redirect
from flask import url_for
from flask.ext.login import login_user
from flask.ext.principal import identity_changed, Identity

from waitlist import db
from waitlist.blueprints.fc_sso import add_sso_handler
from waitlist.sso import authorize, who_am_i
from waitlist.storage.database import Account
from waitlist.utility.eve_id_utils import get_character_by_id_and_name, is_char_banned

logger = logging.getLogger(__name__)


def member_login_cb(code):
    auth = authorize(code)
    access_token = auth['access_token']

    auth_info = who_am_i(access_token)
    char_id = auth_info['CharacterID']
    char_name = auth_info['CharacterName']

    if char_id is None or char_name is None:
        flask.abort(400, "Getting Character from AuthInformation Failed!")

    char = get_character_by_id_and_name(char_id, char_name)

    # see if there is an fc account connected
    acc = db.session.query(Account).filter(
        (Account.username == char.get_eve_name()) & (Account.disabled is False)).first()
    if acc is not None:  # accs are allowed to ignore bans
        login_user(acc, remember=True)
        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(acc.id))
        return redirect(url_for("index"))

    is_banned, reason = is_char_banned(char)
    if is_banned:
        return flask.abort(401, 'You are banned, because your ' + reason + " is banned!")

    login_user(char, remember=True)
    logger.debug("Member Login by %s successful", char.get_eve_name())
    return redirect(url_for("index"))


add_sso_handler('linelogin', member_login_cb)
