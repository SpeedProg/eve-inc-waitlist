import requests
import base64
from waitlist.utility.config import crest_client_id, crest_client_secret
import sys
from nt import access

PY3 = sys.version_info[0] == 3

if PY3:  # pragma: no cover
    string_types = str,
    text_type = str
    binary_type = bytes
else:  # pragma: no cover
    string_types = basestring,
    text_type = unicode
binary_type = str

def text_(s, encoding='latin-1', errors='strict'):
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    return s


def bytes_(s, encoding='latin-1', errors='strict'):
    if isinstance(s, text_type):
        return s.encode(encoding, errors)
    return s

def authorize(code):
    '''{'access_token', 'refresh_token', 'expires_in'}'''
    auth = base64.b64encode(
                ("%s:%s" % (crest_client_id, crest_client_secret))
            )
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