# inject the lib folder before everything else
from waitlist import db
from waitlist.data.names import WaitlistNames
from waitlist.storage.database import Waitlist, WaitlistGroup


def create_default_waitlist_group():
    group = create_waitlist_group("default", "HQ (Default)")
    if group is None:
        return
    group.enabled = True
    group.ordering = 0
    

def create_assault_waitlist_group():
    group = create_waitlist_group("assault", "Assaults")
    if group is None:
        return
    group.ordering = 1


def create_v_g_waitlist_group():
    group = create_waitlist_group("vanguard", "Vanguards")
    if group is None:
        return
    group.ordering = 2


def create_waitlist_group(group_name, display_name):
    # lets check if this group exists
    if db.session.query(WaitlistGroup).filter(WaitlistGroup.groupName == group_name).first() is not None:
        print("Found Group ", group_name)
        return None
    xuplist = Waitlist(name=WaitlistNames.xup_queue, displayTitle="X-UP", waitlistType='xup')
    logilist = Waitlist(name=WaitlistNames.logi, displayTitle="Logi", waitlistType='logi')
    dpslist = Waitlist(name=WaitlistNames.dps, displayTitle="Dps", waitlistType='dps')
    sniperlist = Waitlist(name=WaitlistNames.sniper, displayTitle="Sniper", waitlistType='sniper')
    group = WaitlistGroup()
    group.groupName = group_name
    group.displayName = display_name
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
    create_default_waitlist_group()
    create_assault_waitlist_group()
    create_v_g_waitlist_group()
    db.session.commit()
