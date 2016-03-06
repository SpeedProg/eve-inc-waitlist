from waitlist.storage.database import Role, Waitlist
from waitlist.data.names import WaitlistNames
from waitlist import db


def get_role(name, restrictive=True):
    r = Role()
    r.name = name
    r.is_restrictive = restrictive
    return r

if __name__ == '__main__':
    db.session.create_all()
    # add permissions
    roles = [get_role("admin"), get_role("fc"), get_role("lm"), get_role("resident"), get_role("tbag"), get_role("officer")]
    for role in roles:
        db.session.add(role)
    
    db.session.commit()

    # setup waitlists
    wl_names = [WaitlistNames.logi, WaitlistNames.dps, WaitlistNames.sniper]
    for wl_name in wl_names:
        wl = Waitlist()
        wl.name = wl_name
        db.session.add(wl)
    
    db.session.commit()