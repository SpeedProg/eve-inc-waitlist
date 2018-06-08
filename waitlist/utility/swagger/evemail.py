# https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility
from flask_login import current_user
from pyswagger import App

from waitlist.storage.database import SSOToken

from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve import ESIResponse, get_expire_time, make_error_response
from typing import Dict, List, Any, Sequence

################################
# recipients=[{
# "recipient_id": 0,
# "recipient_type": "character"
# }]
################################
from waitlist.utility.swagger.eve import get_esi_client


def send_mail(token: SSOToken, recipients: List[Dict[str, Any]], body: str, subject: str) -> Any:
    api: App = get_api()
    client = get_esi_client(token, False)

    mail = {
        "approved_cost": 0,
        "body": body,
        "recipients": recipients,
        "subject": subject
    }
    return client.request(api.op['post_characters_character_id_mail'](
        character_id=current_user.current_char, mail=mail))


def open_mail(token: SSOToken, recipients: Sequence[int], body: str, subject: str, to_corp_or_alliance_id: int = None,
              to_mailing_list_id: int = None) -> ESIResponse:
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

    client = get_esi_client(token, False)
    api: App = get_api()
    response = client.request(api.op['post_ui_openwindow_newmail'](new_mail=payload))
    if response.status == 204:
        return ESIResponse(get_expire_time(response), response.status, None)

    return make_error_response(response)
