import logging
from waitlist.base import db
from waitlist.storage.database import Account, SSOToken
logger = logging.getLogger(__name__)

def create_token_cb(accountID):
    def cb(access, expire):
        account = db.session.query(Account).get(accountID)
        if account is None:
            return
        if account.ssoToken == None:
            account.ssoToken = SSOToken(access_token=access, access_token_expires=expire)
        else:
            account.ssoToken.access_token = access
            account.ssoToken.access_token_expires = expire
        db.session.commit()
        return
    return cb