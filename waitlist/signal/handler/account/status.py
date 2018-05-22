from waitlist import db
from waitlist.storage.database import AccountNote
from ... import account_status_change_sig
from waitlist.utility.constants import account_notes


def add_status_change_history_entry(_, account_id: int, by_id: int,
                                    disabled: bool) -> None:

    history_entry = AccountNote(accountID=account_id, byAccountID=by_id,
                                type=account_notes.TYPE_ACCOUNT_ACTIVE_CHANGED
                                )
    history_entry.jsonPayload = {
        'new_disabled': disabled
    }
    db.session.add(history_entry)
    db.session.commit()


def connect() -> None:
    account_status_change_sig.connect(add_status_change_history_entry)
