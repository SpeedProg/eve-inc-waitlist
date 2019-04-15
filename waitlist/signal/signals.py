from blinker.base import Namespace
from typing import Any, Optional
SIG_ROLES_EDITED = 'roles-edited'
SIG_ROLES_ADDED = 'roles-added'
SIG_ROLES_REMOVED = 'roles-removed'
SIG_ACC_CREATED = 'acc-created'
SIG_ACC_STATUS_CHANGE = 'acc-status-change'

SIG_ALT_LINK_REMOVED = 'alt-link-removed'
SIG_ALT_LINK_ADDED = 'alt-link-added'

SIG_ACCOUNT_NAME_CHANGE = 'acc-namec-change'


waitlist_bps = Namespace()


roles_changed_sig = waitlist_bps.\
    signal(SIG_ROLES_EDITED,
           "Called when roles are changed on an account")
account_created_sig = waitlist_bps.\
    signal(SIG_ACC_CREATED,
           'Called when a new Waitlist Account is created')
account_status_change_sig = waitlist_bps.\
    signal(SIG_ACC_STATUS_CHANGE,
           'Called when an account is enabled or disabled')
role_created_sig = waitlist_bps.\
    signal(SIG_ROLES_ADDED,
           'Called when a new role is created')
role_removed_sig = waitlist_bps.\
    signal(SIG_ROLES_REMOVED,
           'Called when a role is removed')

alt_link_removed_sig = waitlist_bps.\
    signal(SIG_ALT_LINK_REMOVED,
           'Called when a link from an account to a character was removed')
alt_link_added_sig = waitlist_bps.\
    signal(SIG_ALT_LINK_ADDED,
           'Called when a link from an account to a character was added')

account_name_change_sig = waitlist_bps.signal(
    'Called when the name of an account gets changed')


def send_roles_changed(sender, to_id, by_id, added_roles, removed_roles, note):
    roles_changed_sig.send(sender, to_id=to_id, by_id=by_id,
                           added_roles=added_roles,
                           removed_roles=removed_roles, note=note)


def send_role_created(sender, by_id, role_name, role_display_name):
    role_created_sig.send(sender, by_id=by_id, role_name=role_name,
                          role_display_name=role_display_name)


def send_role_removed(sender, by_id, role_name, role_display_name):
    role_removed_sig.send(sender, by_id=by_id, role_name=role_name,
                          role_display_name=role_display_name)


def send_account_created(sender, account_id, created_by_id, roles, note):
    """ roles is a string list of role names, not the role database objects """
    account_created_sig.send(sender, account_id=account_id,
                             created_by_id=created_by_id,
                             roles=roles, note=note)


def send_account_status_change(sender, account_id, created_by_id, disabled):
    account_status_change_sig.send(sender, account_id=account_id,
                                   by_id=created_by_id, disabled=disabled)


def send_alt_link_removed(sender, removed_by_id, account_id, character_id):
    alt_link_removed_sig.send(sender, removed_by_id=removed_by_id,
                              account_id=account_id, character_id=character_id)


def send_alt_link_added(sender, added_by_id, account_id, character_id):
    alt_link_added_sig.send(sender, added_by_id=added_by_id,
                            account_id=account_id, character_id=character_id)


def send_account_name_change(sender: Any, by_id: int, account_id: int,
                             old_name: str, new_name: str,
                             note: Optional[str]) -> None:
    account_name_change_sig.send(sender, by_id=by_id, account_id=account_id,
                                 old_name=old_name, new_name=new_name,
                                 note=note)

