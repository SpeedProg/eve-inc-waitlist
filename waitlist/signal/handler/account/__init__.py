from . import created, roles, status


def connect() -> None:
    """
    Connect account signal handler
    """
    created.connect()
    roles.connect()
    status.connect()
