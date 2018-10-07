def is_account(user) -> bool:
    return hasattr(user, 'type') and user.type == "account"


def is_character(user) -> bool:
    return hasattr(user, 'type') and user.type == "character"


def is_account_or_character(user) -> bool:
    return is_account(user) or is_character(user)
