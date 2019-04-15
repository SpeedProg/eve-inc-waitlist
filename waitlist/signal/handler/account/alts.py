from waitlist.storage.database import AccountNote, Character
from waitlist.base import db
from ...signals import alt_link_added_sig, alt_link_removed_sig
from waitlist.utility.constants import account_notes


def on_alt_link_added_history_entry(_, added_by_id: int, account_id: int,
                                    character_id: int) -> None:
    """
    Handler for signal sent when an alt gets added to an account.
    :param added_by_id: id of the account that added the alt
    :param account_id: id of the account the alt was added to
    :param character_id: id of the character that was added as alt
    """
    history_entry = AccountNote(accountID=account_id,
                                byAccountID=added_by_id,
                                type=account_notes.TYPE_ACCOUNT_CHARACTER_LINK_ADDED
                                )
    history_entry.jsonPayload = {'character_id': character_id}

    db.session.add(history_entry)
    db.session.commit()


def on_alt_link_removed_history_entry(_, removed_by_id: int, account_id: int,
                                      character_id: int) -> None:
    """
    Handler for signal sent when an alt gets removed from an account.
    :param added_by_id: id of the account that removed the alt
    :param account_id: id of the account the alt was removed from
    :param character_id: id of the character that was removed as alt
    """
    character: Character = db.session.query(Character).get(character_id)
    history_entry = AccountNote(accountID=account_id,
                                byAccountID=removed_by_id,
                                type=account_notes.TYPE_ACCOUNT_CHARACTER_LINK_REMOVED
                                )
    history_entry.jsonPayload = {'character_id': character.id}

    db.session.add(history_entry)
    db.session.commit()


def connect() -> None:
    """
    Connect singnal handler that create Account Profile notes
    for added an removed alts.
    """
    alt_link_added_sig.connect(on_alt_link_added_history_entry)
    alt_link_removed_sig.connect(on_alt_link_removed_history_entry)
