from waitlist.storage.database import session, Role

def get_role(name):
    r = Role()
    r.name = name
    return r

if __name__ == '__main__':
    # add permissions
    
    roles = [get_role("admin"), get_role("fc"), get_role("lm"), get_role("resident"), get_role("tbag"), get_role("officer")]
    for role in roles:
        session.add(role)
    
    session.commit()
