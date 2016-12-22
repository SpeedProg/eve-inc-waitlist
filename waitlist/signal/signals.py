from blinker.base import Signal
SIG_ROLES_EDITED = "roles-edited"
roles_changed_sig = Signal(SIG_ROLES_EDITED)
def sendRolesChanged(toID, byID, added_roles, removed_roles, note):
    pass