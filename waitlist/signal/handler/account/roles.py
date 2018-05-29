from waitlist.permissions import perm_manager
from ... import roles_changed_sig, role_created_sig
from typing import Iterable, Sequence, Any
from waitlist.storage.database import AccountNote, Role, RoleChangeEntry,\
    Account
from waitlist import db
from sqlalchemy.sql.expression import or_
from waitlist.utility.constants import account_notes


perm_manager.define_permission('trainee')
perm_trainee = perm_manager.get_permission('trainee')


def on_roles_changed_history_entry(_, to_id: int, by_id: int,
                                   added_roles: Sequence[str],
                                   removed_roles: Sequence[str],
                                   note: str) -> None:
    if note == '':
        note = None
    if len(added_roles) <= 0 and len(removed_roles) <= 0 and note == "":
        return
    history_entry = AccountNote(accountID=to_id, byAccountID=by_id, note=note,
                                type=account_notes.TYPE_ACCOUNT_ROLES_CHANGED)
    if len(added_roles) > 0:
        db_roles = db.session.query(Role).filter(
            or_(Role.name == name for name in added_roles)).all()
        for role in db_roles:
            # get role from db
            role_change = RoleChangeEntry(added=True, role=role)
            history_entry.role_changes.append(role_change)

    if len(removed_roles) > 0:
        db_roles = db.session.query(Role).filter(
            or_(Role.name == name for name in removed_roles)).all()
        for role in db_roles:
            role_change = RoleChangeEntry(added=False, role=role)
            history_entry.role_changes.append(role_change)
    db.session.add(history_entry)
    db.session.commit()


# handler to reset welcome mail status
def on_roles_changed_check_welcome_mail(_: Any, to_id: int, by_id: int,
                                        added_roles: Iterable[str],
                                        removed_roles: Iterable[str], note: str) -> None:
    """
    Handler to reset welcome mail status.
    """
    for role in added_roles:
        for need in perm_trainee.needs:
            if role == need.value:
                acc = db.session.query(Account).get(to_id)
                acc.had_welcome_mail = False
                return


def on_role_created_history_entry(_: Any, by_id: int, role_name: str,
                                  role_display_name: str) -> None:

    if by_id is None or role_name is None or role_display_name is None:
        return

    note: AccountNote = AccountNote(accountID=by_id, byAccountID=by_id,
                                    restriction_level=1000,
                                    type=account_notes.TYPE_ROLE_CREATED)
    note.jsonPayload = {
        'role_name': role_name,
        'role_display_name': role_display_name
    }
    db.session.add(note)
    db.session.commit()


def connect() -> None:
    roles_changed_sig.connect(on_roles_changed_history_entry)
    roles_changed_sig.connect(on_roles_changed_check_welcome_mail)
    role_created_sig.connect(on_role_created_history_entry)
