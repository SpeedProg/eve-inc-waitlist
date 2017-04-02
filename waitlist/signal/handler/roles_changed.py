from typing import Iterable, Sequence

from waitlist.permissions import perm_manager
from waitlist.storage.database import AccountNote, RoleChangeEntry
from waitlist import db
from waitlist.storage.database import Role, Account
from sqlalchemy.sql.expression import or_
from waitlist.signal.signals import roles_changed_sig, roles_added_sig

perm_manager.define_permission('trainee')

perm_trainee = perm_manager.get_permission('trainee')


# noinspection PyUnusedLocal
@roles_changed_sig.connect
def on_roles_changed(sender, to_id: int, by_id: int, added_roles: Sequence[str], removed_roles: Sequence[str], note: str) -> None:
    if len(added_roles) <= 0 and len(removed_roles) <= 0 and note == "":
        return
    history_entry = AccountNote(accountID=to_id, byAccountID=by_id, note=note)
    if len(added_roles) > 0:
        db_roles = db.session.query(Role).filter(or_(Role.name == name for name in added_roles)).all()
        for role in db_roles:
            # get role from db
            role_change = RoleChangeEntry(added=True, role=role)
            history_entry.role_changes.append(role_change)
        
    if len(removed_roles) > 0:
        db_roles = db.session.query(Role).filter(or_(Role.name == name for name in removed_roles)).all()
        for role in db_roles:
            role_change = RoleChangeEntry(added=False, role=role)
            history_entry.role_changes.append(role_change)
    db.session.add(history_entry)
    db.session.commit()


# handler to reset welcome mail status
# noinspection PyUnusedLocal
@roles_changed_sig.connect
def on_roles_changed_check_welcome_mail(sender, to_id: int, by_id: int, added_roles: Iterable[str],
                                        removed_roles: Iterable[str], note: str) -> None:
    for role in added_roles:
        for need in perm_trainee.needs:
            if role == need.value:
                acc = db.session.query(Account).get(to_id)
                acc.had_welcome_mail = False
                return


@roles_added_sig.connect
def on_roles_added(sender, by_id: int, role_name: str, role_display_name: str) -> None:

    if by_id is None or role_name is None or role_display_name is None:
        return

    note: AccountNote = AccountNote(accountID=by_id, byAccountID=by_id,
                                    note=f'Added role with name{role_name} and displayName {role_display_name}', restriction_level=1000)
    db.session.add(note)
    db.session.commit()
