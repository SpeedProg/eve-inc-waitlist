from waitlist.signal.signals import account_status_change_sig
from waitlist import db
from waitlist.storage.database import AccountNote


@account_status_change_sig.connect
def add_status_change_note(_, account_id: int, by_id: int, disabled: bool):
    if disabled:
        note = 'Account Deactivated'
    else:
        note = 'Account Activated'

    history_entry = AccountNote(accountID=account_id, byAccountID=by_id, note=note)
    db.session.add(history_entry)
    db.session.commit()
