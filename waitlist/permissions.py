from waitlist.storage.database import Role
from waitlist.setup_wtm import get_role

class WTMRoles():
    admin = get_role("admin")
    officer = get_role("officer")
    fc = get_role("fc")
    lm = get_role("lm")
    tbag = get_role("tbag")
    resident = get_role("resident")
    
