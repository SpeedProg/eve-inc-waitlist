from typing import Dict

import requests
import base64
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
