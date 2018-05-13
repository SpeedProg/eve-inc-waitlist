import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

import flask

from esipy import EsiSecurity
from esipy.events import Signal
from flask_login import current_user

from waitlist import db
from waitlist.storage.database import SSOToken, EveApiScope
from waitlist.utility import config

logger = logging.getLogger(__name__)


def authorize(code: str) -> Dict:
    """
    Get SSO tokens using an SSO auth code.

    :param code: SSO auth code for getting the tokens
    :returns a Dict containing 'access_token', 'refresh_token', 'expires_in'
    """
    security: EsiSecurity = EsiSecurity('', config.crest_client_id, config.crest_client_secret,
                                        headers={'User-Agent': config.user_agent})

    return security.auth(code)


def token_arguement_update_cb(access_token: str, refresh_token: str, expires_at: int,
                              token_identifier: SSOToken, **kwargs: Dict[str, Any]):
    token_identifier.refresh_token = refresh_token
    token_identifier.access_token = access_token
    token_identifier.access_token_expires = datetime.utcfromtimestamp(expires_at)
    logger.debug("Set access_token_expires to %s", token_identifier.access_token_expires)


def who_am_i(token: SSOToken) -> Dict:
    signal = Signal()
    signal.add_receiver(token_arguement_update_cb)

    security: EsiSecurity = EsiSecurity('', config.crest_client_id, config.crest_client_secret,
                                        headers={'User-Agent': config.user_agent},
                                        signal_token_updated=signal,
                                        token_identifier=token
                                        )
    security.update_token(token.info_for_esi_security())

    return security.verify()


def add_token(code):
    """
    Adds a token to the current Account using the given SSO code
    :param code: SSO auth code to use to get token info
    """
    tokens = authorize(code)
    re_token = tokens['refresh_token']
    acc_token = tokens['access_token']
    exp_in = int(tokens['expires_in'])

    token: SSOToken = SSOToken(refresh_token=re_token, access_token=acc_token,
                               accountID=current_user.id,
                               access_token_expires=(datetime.utcnow() + timedelta(seconds=exp_in)))

    auth_info = who_am_i(token)
    char_name = auth_info['CharacterName']
    char_id = auth_info['CharacterID']
    if char_name != current_user.get_eve_name():
        flask.abort(409, 'You did not grant authorization for the right character "' + current_user.get_eve_name() +
                    '". Instead you granted it for "' + char_name + '"')

    scopenames = auth_info['Scopes'].split(' ')

    token.characterID = char_id

    for scope_name in scopenames:
        token.scopes.append(EveApiScope(scopeName=scope_name))

    current_user.add_sso_token(token)

    db.session.commit()