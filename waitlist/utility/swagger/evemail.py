# https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility
from flask_login import current_user
from esipy.security import EsiSecurity
from pyswagger import App

from waitlist.utility.config import crest_return_url, crest_client_id,\
    crest_client_secret
from datetime import datetime

from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve import ESIResponse, get_expire_time
from typing import Dict, List, Any, Sequence

################################
# recipients=[{
# "recipient_id": 0,
# "recipient_type": "character"
# }]
################################
from waitlist.utility.swagger.eve import get_esi_client
from waitlist.utility.swagger.patch import EsiClient


def sendMail(recipients: List[Dict[str, Any]], body: str, subject: str) -> Any:
    api: App = get_api('v1')
    security = EsiSecurity(
        api,
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': current_user.ssoToken.access_token,
        'expires_in': (current_user.ssoToken.access_token_expires -
                       datetime.utcnow()).total_seconds(),
        'refresh_token': current_user.ssoToken.refresh_token
    })

    client = EsiClient(security, timeout=10)

    mail = {
        "approved_cost": 0,
        "body": body,
        "recipients": recipients,
        "subject": subject
    }
    return client.request(api.op['post_characters_character_id_mail'](
        character_id=current_user.current_char, mail=mail))

def openMail(recipients: Sequence[int], body: str, subject: str, to_corp_or_alliance_id: int = None, to_mailing_list_id: int = None) -> ESIResponse:
    """
    {
        "body": "string",
        "recipients": [
            0 # min 1 item
        ],
        "subject": "string",
        "to_corp_or_alliance_id": 0, # optional
        "to_mailing_list_id": 0 # optional
        # max 1 of the 2 optimal values
    }
    """
    payload: Dict[str, Any] = {}
    if to_corp_or_alliance_id is not None and to_mailing_list_id is not None:
        raise ValueError("Only to_mailing_list_id or to_corp_or_alliance_id can have a value, not both!")

    payload['body'] = body
    payload['subject'] = subject
    if to_mailing_list_id is not None:
        payload['to_mailing_list_id'] = to_mailing_list_id

    if to_corp_or_alliance_id is not None:
        payload['to_corp_or_alliance_id'] = to_corp_or_alliance_id

    payload['recipients'] = []

    for charID in recipients:
        payload['recipients'].append(charID)

    if len(payload['recipients']) <= 0:
        payload['recipients'] = [0]

    client = get_esi_client('v1')
    response = client.request(client.security.app.op['post_ui_openwindow_newmail'](new_mail=payload))
    if response.status == 204:
        return ESIResponse(get_expire_time(response), response.status, None)

    return ESIResponse(get_expire_time(response), response.status, response.data['error'])
