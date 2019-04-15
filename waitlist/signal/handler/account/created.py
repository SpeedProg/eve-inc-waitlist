from ... import account_created_sig
from waitlist.storage.database import AccountNote, Role, RoleChangeEntry
from typing import Sequence
from waitlist.base import db
from sqlalchemy.sql.expression import or_
from waitlist.utility.constants import account_notes


def on_account_created_history_entry(_, account_id: int, created_by_id: int,
                                     roles: Sequence[str], note: str):
    if note == '':
        note = None

    history_entry = AccountNote(accountID=account_id,
                                byAccountID=created_by_id,
                                note=note,
                                type=account_notes.TYPE_ACCOUNT_CREATED)
    if len(roles) > 0:
        db_roles = db.session.query(Role).filter(
            or_(Role.name == name for name in roles)).all()
        for role in db_roles:
            # get role from db
            role_change = RoleChangeEntry(added=True, role=role)
            history_entry.role_changes.append(role_change)

    db.session.add(history_entry)
    db.session.commit()


def connect():
    account_created_sig.connect(on_account_created_history_entry)
