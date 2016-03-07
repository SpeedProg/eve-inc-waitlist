from waitlist.storage.database import Role, Waitlist
from waitlist.data.names import WaitlistNames, WTMRoles
from waitlist import db


def get_role(name, restrictive=True):
    r = Role()
    r.name = name
    r.is_restrictive = restrictive
    return r

def createRoles():
    roles = [get_role(WTMRoles.admin), get_role(WTMRoles.officer), get_role(WTMRoles.lm), get_role(WTMRoles.resident), get_role(WTMRoles.fc), get_role(WTMRoles.tbadge)]
    for role in roles:
        db.session.add(role)

def createWaitlists():
    wl_names = [WaitlistNames.logi, WaitlistNames.dps, WaitlistNames.sniper, Waitlist.xup_queue]
    for wl_name in wl_names:
        wl = Waitlist()
        wl.name = wl_name
        db.session.add(wl)

if __name__ == '__main__':
    #createRoles()
    #createWaitlists()    
    #db.session.commit()
    pass