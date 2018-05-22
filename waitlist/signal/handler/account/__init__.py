from . import created, roles, status, alts


def connect() -> None:
    """
    Connect account signal handler
    """
    created.connect()
    roles.connect()
    status.connect()
    alts.connect()
