from blinker.base import Namespace
SIG_ROLES_EDITED = "roles-edited"

waitlist_bps = Namespace();

roles_changed_sig = waitlist_bps.signal(SIG_ROLES_EDITED, "Called when roles are changed on an account")
def sendRolesChanged(sender, toID, byID, added_roles, removed_roles, note):
    roles_changed_sig.send(sender, toID=toID, byID=byID, added_roles=added_roles, removed_roles=removed_roles, note=note)