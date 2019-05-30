from . import account_changes

def connect() -> None:
    """
    Connect murmur signal handler
    """
    account_changes.connect()

