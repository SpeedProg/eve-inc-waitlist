from datetime import datetime
import logging
from ...signals import fleet_removed_last_sig, fleet_removed_sig, fleet_added_first_sig
from ....utility.timetracking import tracker


logger = logging.getLogger(__name__)


def on_first_fleet_created(_, fleet_id: int) -> None:
    logger.info('Got on_first_fleet_created')
    tracker.start_tracking()


def on_last_fleet_removed(_, fleet_id: int) -> None:
    logger.info('Got on_last_fleet_removed')
    tracker.stop_tracking()


def on_fleet_removed(_, fleet_id: int, creation_time: datetime) -> None:
    logger.info('Got on_fleet_removed')
    tracker.fleet_removed(fleet_id, creation_time)


def connect() -> None:
    """
    Connect singnal handler that controle time timetracking
    """
    logger.info('Registering handlers for timetracking')
    fleet_added_first_sig.connect(on_first_fleet_created)
    fleet_removed_last_sig.connect(on_last_fleet_removed)
    fleet_removed_sig.connect(on_fleet_removed)
