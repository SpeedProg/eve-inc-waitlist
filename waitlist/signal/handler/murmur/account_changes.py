from typing import Optional, Any
from ...signals import default_char_change_sig, roles_changed_sig, account_status_change_sig
from waitlist.utility.murmur.connector import MurmurConnector
from waitlist.utility.eve_id_utils import get_character_by_id
from waitlist.storage.database import Character, Account

def on_default_char_change_update_murmur(sender, by_id: int, account_id:int,
                                         old_char_id: Optional[int], new_char_id: Optional[int],
                                         note: Optional[str]) -> None:
    """Make sure the murmur data gets updated if they change their default character
    """
    if new_char_id is None:
        return

    char: Character = get_character_by_id(new_char_id)
    con: MurmurConnector = MurmurConnector()
    con.update_user_rights(account_id, char.eve_name)


def on_roles_changed_update_murmur(sender, to_id: int, by_id: int,
                                   added_roles, removed_roles, note) -> None:
    con: MurmurConnector = MurmurConnector()
    acc: Account = Account.query.get(to_id)
    con.update_user_rights(to_id, acc.get_eve_name())


def on_account_status_change_update_murmur(sender: Any, account_id: int,
                                           by_id: int, disabled: bool) -> None:
    con: MurmurConnector = MurmurConnector()
    if disabled:
        con.update_user_rights(account_id, '')  # this should remove the account from murmur


def connect() -> None:
    """Connect signal handlers
    """
    #default_char_change_sig.connect(on_default_char_change_update_murmur)
    roles_changed_sig.connect(on_roles_changed_update_murmur)
    account_status_change_sig.connect(on_account_status_change_update_murmur)

