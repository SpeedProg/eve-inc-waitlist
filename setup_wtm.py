# inject the lib folder before everything else
import os
import sys
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist.storage.database import Role, Waitlist, WaitlistGroup
from waitlist.data.names import WaitlistNames, WTMRoles
from waitlist.base import db


def get_role(name):
    r = Role()
    r.name = name
    r.displayName = WTMRoles.get_display_name(name)
    return r

def createRoles():
    role_list = WTMRoles.get_role_list()

    existing_roles = db.session.query(Role).all()

    for role_name in role_list:
        exists = False
        for dbrole in existing_roles:
            if dbrole.name == role_name:
                exists = True
                print("Found roles ", role_name)
                break
        if not exists:
            db.session.add(get_role(role_name))

def createDefaultWaitlistGroup():
    group = createWaitlistGroup("default", "HQ (Default)")
    if group is None:
        return
    group.enabled = True
    group.ordering = 0
    

def createAssaultWaitlistGroup():
    group = createWaitlistGroup("assault", "Assaults")
    if group is None:
        return
    group.ordering = 1

def createVGWaitlistGroup():
    group = createWaitlistGroup("vanguard", "Vanguards")
    if group is None:
        return
    group.ordering = 2
    
def createWaitlistGroup(groupName, displayName):
    # lets check if this group exists
    if db.session.query(WaitlistGroup).filter(WaitlistGroup.groupName == groupName).first() != None:
        print("Found Group ", groupName)
        return None
    xuplist = Waitlist(name=WaitlistNames.xup_queue, displayTitle="X-UP")
    logilist = Waitlist(name=WaitlistNames.logi, displayTitle="Logi")
    dpslist = Waitlist(name=WaitlistNames.dps, displayTitle="Dps")
    sniperlist = Waitlist(name=WaitlistNames.sniper, displayTitle="Sniper")
    group = WaitlistGroup()
    group.groupName = groupName
    group.displayName = displayName
    group.xuplist = xuplist
    group.logilist = logilist
    group.dpslist = dpslist
    group.sniperlist = sniperlist
    group.otherlist = None
    group.enabled = False
    db.session.add(group)
    db.session.flush()
    db.session.refresh(group)
    
    xuplist.group = group
    logilist.group = group
    dpslist.group = group
    sniperlist.group = group
    return group

if __name__ == '__main__':
    createRoles()
    createDefaultWaitlistGroup()
    createAssaultWaitlistGroup()
    createVGWaitlistGroup()
    db.session.commit()
    pass