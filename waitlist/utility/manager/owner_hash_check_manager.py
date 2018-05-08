import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Union, List

from esipy import EsiSecurity
from esipy.exceptions import APIException

from waitlist import db
from waitlist.sso import who_am_i
from waitlist.storage.database import Account, Character, SSOToken, EveApiScope
from waitlist.utility import config

logger = logging.getLogger(__name__)


class OwnerHashCheckManager():
    """
    Manager for checking owner hash
    """

    def __init(self):
        self.last_owner_hash_check_lookup: Dict[int, datetime] = dict()
        pass

    def need_new_ownerhash_check(self, character_id: int) -> bool:
        if character_id in self.last_owner_hash_check_lookup:
            last_check: datetime = self.last_owner_hash_check_lookup[character_id]
            # if the last check was before the last downtime do a check
            if last_check < self.get_last_downtime():
                return True
            return False

        return True

    def set_last_successful_owner_hash_check(self, character_id: int) -> None:
        self.last_owner_hash_check_lookup[character_id] = datetime.now(timezone.utc)

    def is_ownerhash_valid(self, user: Union[Character, Account]) -> bool:
        char_id: int = user.get_eve_id()

        if not self.need_new_ownerhash_check(char_id):
            logger.debug("We already did the owner_hash check since last downtime")
            return True

        if user.sso_token is None:
            logger.info("%s sso_token is None, owner_hash check failed", user)
            return False

        security = EsiSecurity('', client_id=config.crest_client_id, secret_key=config.crest_client_secret)
        security.refresh_token = user.sso_token.refresh_token
        try:
            security.refresh()

            # the token still works
            auth_info = who_am_i(security.access_token)
            owner_hash = auth_info['CharacterOwnerHash']
            scopes = auth_info['Scopes']

            OwnerHashCheckManager.set_token_data(user.sso_token, security.access_token, security.refresh_token,
                                                 datetime.fromtimestamp(security.token_expiry), scopes)
            db.session.commit()
            if owner_hash != user.owner_hash:
                logger.info("%s owner_hash did not match, force logout and invalidate all sessions", user)
                return False

            # owner hash still matches
            self.set_last_successful_owner_hash_check(char_id)
            logger.debug("%s owner_hash did match, let the request continue", user)
            return True

        except APIException as e:
            # if this happens the token doesn't work anymore
            # => owner probably changed or for other reason
            logger.exception("API Error during token validation, invalidating all sessions and forcing logout", e)
            return False


    @staticmethod
    def get_last_downtime() -> datetime:
        # get current utc time
        current_time = datetime.utcnow()
        # downtime is at 11:00 UTC every day
        if current_time.hour < 11:
            # last downtime was 11 utc 1 day earlier
            current_time -= timedelta(days=1)

        # if we are past dt, dt was today at 11 UTC no need to substract
        current_time = current_time.replace(hour=11, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        return current_time

    @staticmethod
    def set_token_data(token: SSOToken, access_token: str, refresh_token: str, expires_at: datetime,
                       scopes: str) -> None:
        """
        :param scopes space seperated list of scopes
        """

        token.access_token = access_token
        token.refresh_token = refresh_token
        token.access_token_expires = expires_at
        scope_name_list: List[str] = scopes.split(" ")
        token_scopes: List[EveApiScope] = []

        for scope_name in scope_name_list:
            token_scopes.append(EveApiScope(scopeName=scope_name))

        token.scopes = token_scopes


owner_hash_check_manager = OwnerHashCheckManager()