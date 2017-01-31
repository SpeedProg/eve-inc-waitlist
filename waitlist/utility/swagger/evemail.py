# https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility
from flask_login import current_user
from esipy.security import EsiSecurity
from waitlist.utility.config import crest_return_url, crest_client_id,\
    crest_client_secret
from esipy.client import EsiClient
from datetime import datetime
from waitlist.utility.swagger import api

#
#recipients=[{
#"recipient_id": 0,
#"recipient_type": "character"
#}]
#
def sendMail(recipients, body, subject):
    security = EsiSecurity(
        api,
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': current_user.ssoToken.access_token,
        'expires_in': (current_user.ssoToken.access_token_expires - datetime.utcnow()).total_seconds(),
        'refresh_token': current_user.ssoToken.refresh_token
    })
    #security.auth(current_user.ssoToken.access_token)
    client = EsiClient(security)
    
    mail= {
        "approved_cost": 0,
        "body": body,
        "recipients": recipients,
        "subject": subject
    }
    return client.request(api.op['post_characters_character_id_mail'](character_id=current_user.current_char, mail=mail))
