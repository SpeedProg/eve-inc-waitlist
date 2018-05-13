import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Union, Optional

from waitlist import db
from waitlist.sso import who_am_i
from waitlist.storage.database import Account, Character, SSOToken

logger = logging.getLogger(__name__)


class OwnerHashCheckManager():
    """
    Manager for checking owner hash
    """

    def __init__(self):
        self.last_owner_hash_check_lookup: Dict[int, datetime] = dict()

    def need_new_ownerhash_check(self, character_id: int) -> bool:
        """
        Check if this characters owner_hash was check successfully since last downtime
        :param character_id: the id of the character
        :return: True if the character's owner_hash was not checked successfully since the last downtime
        """
        if character_id in self.last_owner_hash_check_lookup:
            last_check: datetime = self.last_owner_hash_check_lookup[character_id]
            # if the last check was before the last downtime do a check
            if last_check < self.get_last_downtime():
                return True
            return False

        return True

    def set_last_successful_owner_hash_check(self, character_id: int) -> None:
        """
        Set the last successful owner_hash check time to now
        :param character_id: Id of the character to check for
        :return: Nothing
        """
        self.last_owner_hash_check_lookup[character_id] = datetime.now(timezone.utc)

    def is_alt_ownerhash_valid(self, account: Account, character: Character) -> bool:
        """
        Checks if the owner_hash of the given character connected with the given account is valid
        :param account: the account the character is connected too
        :param character: the character to check the owner_hash of
        :return: True if the owner_hash is valid otherwise False
        """
        if not self.need_new_ownerhash_check(character.id):
            return True

        token: Optional[SSOToken] = account.get_a_sso_token_with_scopes([])

        if token is None:
            return False

        # the token still works
        auth_info = who_am_i(token)
        owner_hash = auth_info['CharacterOwnerHash']

        # possible token update happened
        db.session.commit()
        if owner_hash != character.owner_hash:
            logger.info("%s owner_hash did not match", character)
            return False

        # owner hash still matches
        self.set_last_successful_owner_hash_check(character.id)
        logger.debug("%s and %s owner_hash did match", account, character)
        return True

    def is_ownerhash_valid(self, user: Union[Character, Account]) -> bool:
        """
        Checks if the owner_hash and the SSOToken of the given character or character set on the account,
        connected with the given account is valid
        This also updates the token data.
        :param user: Character or Account to check the owner_hash/token validity off
        :return: True if the owner_hash is valid otherwise False
        an Account with no set current character is always valid
        """
        char_id: int = user.get_eve_id()
        if char_id is None:
            return True
        if not self.need_new_ownerhash_check(char_id):
            logger.debug("We already did the owner_hash check since last downtime")
            return True

        token: Optional[SSOToken] = user.get_a_sso_token_with_scopes([])

        if token is None:
            if hasattr(user, 'current_char'):
                logger.debug("%s no valid sso token with character %s, owner_hash check failed", user, user.current_char)
            else:
                logger.debug("%s no valid sso token , owner_hash check failed", user)
            return False

        # the token still works
        auth_info = who_am_i(token)
        owner_hash = auth_info['CharacterOwnerHash']
        # possible token update happened
        db.session.commit()

        if owner_hash != user.owner_hash:
            logger.info("%s's new owner_hash %s did not match owner_hash in database %s", user, owner_hash,  user.owner_hash)
            return False

        # owner hash still matches
        self.set_last_successful_owner_hash_check(char_id)
        logger.debug("%s owner_hash did match, let the request continue", user)
        return True

    @staticmethod
    def is_auth_valid_for_token(token: Optional[SSOToken]) -> bool:
        """
        Checks if a token still works, returns an EsiSecurity object that .refresh() was used on
        or None if the token doesn't work anymore
        :param token: a token to check or None
        :return: True if the token is still valid otherwise False
        """
        if token is None:
            logger.debug("token is not valid")
            return False

        return token.is_valid

    @staticmethod
    def is_auth_valid_for_account_character_pair(account: Account, character: Character) -> bool:
        """
        Checks if a token still works, returns an EsiSecurity object that .refresh() was used on
        or None if the token doesn't work anymore
        :param account: the account the token should be connected to
        :param character: the character the token should be connected to
        :return: True if the token is valid otherwise False
        """
        # does a valid token exist for this character+account combo
        return OwnerHashCheckManager.is_auth_valid_for_token(account.get_token_for_charid(character.id))

    @staticmethod
    def get_last_downtime() -> datetime:
        """
        Get the datetime the last downtime occurred
        :return: The datetime of the last downtime
        """
        # get current utc time
        current_time = datetime.utcnow()
        # downtime is at 11:00 UTC every day
        if current_time.hour < 11:
            # last downtime was 11 utc 1 day earlier
            current_time -= timedelta(days=1)

        # if we are past dt, dt was today at 11 UTC no need to substract
        current_time = current_time.replace(hour=11, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        return current_time


owner_hash_check_manager = OwnerHashCheckManager()