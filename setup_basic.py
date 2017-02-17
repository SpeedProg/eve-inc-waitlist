import os
import sys
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from typing import List

from waitlist import db
from waitlist.storage.database import EveApiScope

api_scopes: List[str] = ['esi-ui.open_window.v1', 'esi-fleets.read_fleet.v1', 'esi-fleets.write_fleet.v1', 'esi-mail.send_mail.v1']


def create_roles():
    for scope in api_scopes:
        dbscope = db.session.query(EveApiScope).filter(EveApiScope.scopeName == scope).first()
        if dbscope == None:
            dbscope = EveApiScope(scopeName=scope)
            db.session.add(dbscope)

if __name__ == '__main__':
    create_roles()
    db.session.commit()