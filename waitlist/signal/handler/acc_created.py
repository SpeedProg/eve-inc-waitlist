from waitlist.storage.database import RoleHistoryEntry, RoleChangeEntry#
from waitlist.base import db
from waitlist.storage.database import Role
from sqlalchemy.sql.expression import or_
from waitlist.signal.signals import account_created_sig

@account_created_sig.connect
def onAccountCreated(sender, accountID, createdByID, roles, note):
    historyEntry = RoleHistoryEntry(accountID=accountID, byAccountID=createdByID, note=note)
    if len(roles) > 0:
        db_roles = db.session.query(Role).filter(or_(Role.name == name for name in roles)).all()
        for role in db_roles:
            # get role from db
            role_change = RoleChangeEntry(added=True, role=role)
            historyEntry.role_changes.append(role_change)

    db.session.add(historyEntry)
    db.session.commit()