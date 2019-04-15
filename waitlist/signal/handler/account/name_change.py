from waitlist.base import db
from waitlist.storage.database import AccountNote
from waitlist.utility.constants import account_notes
from typing import Optional
from ... import account_name_change_sig


def add_name_change_history_entry(_, by_id: int, account_id: int,
                                  old_name: str, new_name: str,
                                  note: Optional[str]) -> None:
    if note == '':
        note = None
    history_entry = AccountNote(accountID=account_id, byAccountID=by_id,
                                type=account_notes.TYPE_ACCOUNT_NAME_CHANGED,
                                note=note)
    history_entry.jsonPayload = {
        'old_name': old_name,
        'new_name': new_name
    }
    db.session.add(history_entry)
    db.session.commit()


def connect() -> None:
    account_name_change_sig.connect(add_name_change_history_entry)
