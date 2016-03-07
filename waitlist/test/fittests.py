from waitlist.data.names import WTMRoles
from waitlist.storage.database import Role
from waitlist import db
if __name__ == '__main__':
    r = Role()
    r.name = WTMRoles.dev
    r.is_restrictive = True
    
    db.session.add(r)
    db.session.commit()
    