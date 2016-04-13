# inject the lib folder before everything else
import os
import sys
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist.storage.database import Role, Waitlist, WaitlistGroup
from waitlist.data.names import WaitlistNames, WTMRoles, DEFAULT_PREFIX
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

def createDefaultWaitlistGroup():
    xuplist = Waitlist(name=WaitlistNames.xup_queue, displayTitle="X-UP")
    logilist = Waitlist(name=WaitlistNames.logi, displayTitle="Logi")
    dpslist = Waitlist(name=WaitlistNames.dps, displayTitle="DPS")
    sniperlist = Waitlist(name=WaitlistNames.sniper, displayTitle="SNIPER")
    group = WaitlistGroup()
    group.groupName = "default"
    group.displayName = "Headquarters"
    group.xuplist = xuplist
    group.logilist = logilist
    group.dpslist = dpslist
    group.sniperlist = sniperlist
    group.otherlist = None
    db.session.add(group)
    db.session.flush()
    db.session.refresh(group)
    
    xuplist.group = group
    logilist.group = group
    dpslist.group = group
    sniperlist.group = group
    

if __name__ == '__main__':
    #createRoles()
    createDefaultWaitlistGroup()
    db.session.commit()
    pass