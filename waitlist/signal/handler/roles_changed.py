from waitlist.storage.database import AccountNote, RoleChangeEntry#
from waitlist.base import db
from waitlist.storage.database import Role
from sqlalchemy.sql.expression import or_
from waitlist.signal.signals import roles_changed_sig

@roles_changed_sig.connect
def onRolesChanged(sender, toID, byID, added_roles, removed_roles, note):
    if (len(added_roles) <= 0 and len(removed_roles) <= 0 and note == ""):
        return
    historyEntry = AccountNote(accountID=toID, byAccountID=byID, note=note)
    if len(added_roles) > 0:
        db_roles = db.session.query(Role).filter(or_(Role.name == name for name in added_roles)).all()
        for role in db_roles:
            # get role from db
            role_change = RoleChangeEntry(added=True, role=role)
            historyEntry.role_changes.append(role_change)
        
    if len(removed_roles) > 0:
        db_roles = db.session.query(Role).filter(or_(Role.name == name for name in removed_roles)).all()
        for role in db_roles:
            role_change = RoleChangeEntry(added=False, role=role)
            historyEntry.role_changes.append(role_change)
    db.session.add(historyEntry)
    db.session.commit()