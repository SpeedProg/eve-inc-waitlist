import requests
import base64
from waitlist.utility.config import crest_client_id, crest_client_secret
import sys

PY3 = sys.version_info[0] == 3

if PY3:  # pragma: no cover
    string_types = str,
    text_type = str
    binary_type = bytes
else:  # pragma: no cover
    string_types = str,
    text_type = str
binary_type = str

def authorize(code):
    '''{'access_token', 'refresh_token', 'expires_in'}'''
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
        raise Exception("Authentication Failed with %d", res.status_code)
    
    return res.json()

def whoAmI(access_token):#
    url = 'https://login.eveonline.com/oauth/verify'
    response = requests.get(url, headers={'Authorization': "Bearer " + access_token})
    return response.json()