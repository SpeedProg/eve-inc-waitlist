from typing import Optional


def get_locale_code(user) -> Optional[str]:
    from .types import is_account_or_character
    if is_account_or_character(user):
        return user.language
    return None


def set_locale_code(user, code: str) -> None:
    from .types import is_account_or_character
    if is_account_or_character(user):
        user.language = code
