from . import created, roles, status, alts, name_change


def connect() -> None:
    """
    Connect account signal handler
    """
    created.connect()
    roles.connect()
    status.connect()
    alts.connect()
    name_change.connect()
