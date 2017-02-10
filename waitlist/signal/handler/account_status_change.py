from waitlist.signal.signals import account_status_change_sig
from waitlist.storage.database import RoleChangeEntry#
from waitlist.base import db
from waitlist.storage.database import Role, AccountNote
from sqlalchemy.sql.expression import or_

@account_status_change_sig.connect
def addStatusChangeNote(sender, accountID, byID, disabled):

    note = ''
    if disabled:
        note = 'Account Deactivated'
    else:
        note = 'Account Activated'

    historyEntry = AccountNote(accountID=accountID, byAccountID=byID, note=note)
    db.session.add(historyEntry)
    db.session.commit()