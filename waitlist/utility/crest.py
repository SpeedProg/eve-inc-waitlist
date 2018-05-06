import logging
from waitlist import db
from waitlist.storage.database import Account, SSOToken
logger = logging.getLogger(__name__)


def create_token_cb(account_id):
    def cb(access, expire):
        account = db.session.query(Account).get(account_id)
        if account is None:
            return
        if account.sso_token is None:
            account.sso_token = SSOToken(access_token=access, access_token_expires=expire)
        else:
            account.sso_token.access_token = access
            account.sso_token.access_token_expires = expire
        db.session.commit()
        return
    return cb
