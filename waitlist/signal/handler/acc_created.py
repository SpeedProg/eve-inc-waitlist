from typing import Sequence

from waitlist.storage.database import RoleChangeEntry  #
from waitlist import db
from waitlist.storage.database import Role, AccountNote
from sqlalchemy.sql.expression import or_
from waitlist.signal.signals import account_created_sig


@account_created_sig.connect
def on_account_created(_, account_id: int, created_by_id: int, roles: Sequence[str], note):
    history_entry = AccountNote(accountID=account_id, byAccountID=created_by_id, note=note)
    if len(roles) > 0:
        db_roles = db.session.query(Role).filter(or_(Role.name == name for name in roles)).all()
        for role in db_roles:
            # get role from db
            role_change = RoleChangeEntry(added=True, role=role)
            history_entry.role_changes.append(role_change)

    db.session.add(history_entry)
    db.session.commit()
