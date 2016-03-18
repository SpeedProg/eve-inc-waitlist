# inject the lib folder before everything else
import os
import sys
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist.storage.database import Role, Waitlist
from waitlist.data.names import WaitlistNames, WTMRoles
from waitlist import db


def get_role(name, restrictive=True):
    r = Role()
    r.name = name
    r.is_restrictive = restrictive
    return r

def createRoles():
    role_list = WTMRoles.get_role_list()
    roles = []
    for role in role_list:
        roles.append(get_role(role))

    for role in roles:
        db.session.merge(role)

def createWaitlists():
    wl_names = [WaitlistNames.logi, WaitlistNames.dps, WaitlistNames.sniper, WaitlistNames.xup_queue]
    for wl_name in wl_names:
        wl = Waitlist()
        wl.name = wl_name
        db.session.merge(wl)

if __name__ == '__main__':
    createRoles()
    createWaitlists()    
    db.session.commit()
    pass