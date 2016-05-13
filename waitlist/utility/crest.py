import logging
from waitlist.base import db
from waitlist.storage.database import Account
logger = logging.getLogger(__name__)

def create_token_cb(accountID):
    def cb(access, expire):
        account = db.session.query(Account).get(accountID)
        if account is None:
            return
        account.access_token = access
        account.access_token_expires = expire
        db.session.commit()
        return
    return cb