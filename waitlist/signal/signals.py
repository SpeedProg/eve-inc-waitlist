from blinker.base import Namespace
SIG_ROLES_EDITED = 'roles-edited'
SIG_ACC_CREATED = 'acc-created'

waitlist_bps = Namespace();

roles_changed_sig = waitlist_bps.signal(SIG_ROLES_EDITED, "Called when roles are changed on an account")
def sendRolesChanged(sender, toID, byID, added_roles, removed_roles, note):
    roles_changed_sig.send(sender, toID=toID, byID=byID, added_roles=added_roles, removed_roles=removed_roles, note=note)

account_created_sig = waitlist_bps.signal(SIG_ACC_CREATED, 'Called when a new Waitlist Account is created')
def sendAccountCreated(sender, accountID, createdByID, roles, note):
    ''' roles is a string list of role names, not the role database objects '''
    account_created_sig.send(sender, accountID=accountID, createdByID=createdByID, roles=roles, note=note)