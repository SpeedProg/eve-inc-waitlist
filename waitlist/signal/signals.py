from blinker.base import Namespace
SIG_ROLES_EDITED = 'roles-edited'
SIG_ACC_CREATED = 'acc-created'
SIG_ACC_STATUS_CHANGE = 'acc-status-change'

waitlist_bps = Namespace()

roles_changed_sig = waitlist_bps.signal(SIG_ROLES_EDITED, "Called when roles are changed on an account")
account_created_sig = waitlist_bps.signal(SIG_ACC_CREATED, 'Called when a new Waitlist Account is created')
account_status_change_sig = waitlist_bps.signal(SIG_ACC_STATUS_CHANGE, 'Called when an account is enabled or disabled')


def send_roles_changed(sender, to_id, by_id, added_roles, removed_roles, note):
    roles_changed_sig.send(sender, toID=to_id, byID=by_id, added_roles=added_roles,
                           removed_roles=removed_roles, note=note)


def send_account_created(sender, account_id, created_by_id, roles, note):
    """ roles is a string list of role names, not the role database objects """
    account_created_sig.send(sender, accountID=account_id, createdByID=created_by_id, roles=roles, note=note)


def send_account_status_change(sender, account_id, created_by_id):
    account_status_change_sig.send(sender, accountID=account_id, byID=created_by_id, disabled=True)
