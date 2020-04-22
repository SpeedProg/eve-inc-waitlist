from . import fleet


def connect() -> None:
    """
    Connect to fleet signals to make tracking react to it
    """
    fleet.connect()
