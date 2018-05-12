from datetime import datetime, timedelta
from typing import Dict

import flask
import requests
import base64

from flask_login import current_user

from waitlist import db
from waitlist.storage.database import SSOToken, EveApiScope
from waitlist.utility.config import crest_client_id, crest_client_secret


def authorize(code: str) -> Dict:
    """{'access_token', 'refresh_token', 'expires_in'}"""
    auth = base64.b64encode(
                ("%s:%s" % (crest_client_id, crest_client_secret)).encode('utf-8', 'strict')
            ).decode('utf-8', 'strict')
    headers = {"Authorization": "Basic %s" % auth}
    url = "https://login.eveonline.com/oauth/token"
    params = {
                "grant_type": "authorization_code",
                "code": code
            }
    res = requests.post(url, params=params, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Authentication Failed with { res.status_code }")
    
    return res.json()


def who_am_i(access_token: str) -> Dict:
    url = 'https://login.eveonline.com/oauth/verify'
    response = requests.get(url, headers={'Authorization': "Bearer " + access_token})
    return response.json()


def add_token(code):
    """
    Adds a token to the current Account using the given SSO code
    """
    tokens = authorize(code)
    re_token = tokens['refresh_token']
    acc_token = tokens['access_token']
    exp_in = int(tokens['expires_in'])

    auth_info = who_am_i(acc_token)
    char_name = auth_info['CharacterName']
    char_id = auth_info['CharacterID']
    if char_name != current_user.get_eve_name():
        flask.abort(409, 'You did not grant authorization for the right character "' + current_user.get_eve_name() +
                    '". Instead you granted it for "' + char_name + '"')

    scopenames = auth_info['Scopes'].split(' ')
    token: SSOToken = SSOToken(refresh_token=re_token, access_token=acc_token,
                               accountID = current_user.id, characterID = char_id,
                             access_token_expires=(datetime.utcnow() + timedelta(seconds=exp_in)))

    for scope_name in scopenames:
        token.scopes.append(EveApiScope(scopeName=scope_name))

    current_user.add_sso_token(token)

    db.session.commit()