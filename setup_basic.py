import os
import sys
from waitlist.base import db
from waitlist.storage.database import EveApiScope
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))

api_scopes = ['fleetRead', 'fleetWrite', 'remoteClientUI', 'esi-mail.send_mail.v1']

def createRoles():
    for scope in api_scopes:
        dbscope = db.session.query(EveApiScope).filter(EveApiScope.scopeName == scope).first()
        if dbscope == None:
            dbscope = EveApiScope(scopeName=scope)
            db.session.add(dbscope)

if __name__ == '__main__':
    createRoles()
    db.session.commit()