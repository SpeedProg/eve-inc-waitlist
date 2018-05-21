from waitlist import db
from waitlist.storage.database import AccountNote
from ... import account_status_change_sig


def add_status_change_history_entry(_, account_id: int, by_id: int,
                                    disabled: bool) -> None:
    if disabled:
        note = 'Account Deactivated'
    else:
        note = 'Account Activated'

    history_entry = AccountNote(accountID=account_id, byAccountID=by_id,
                                note=note)
    db.session.add(history_entry)
    db.session.commit()


def connect() -> None:
    account_status_change_sig.connect(add_status_change_history_entry)
