from waitlist.utility.swagger.eve import ESIResponse
from waitlist.utility.swagger.eve.fleet.models import FleetMember, EveFleetWing
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EveFleetMembers(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str],
                 data: Optional[List[Dict[str, Any]]]) -> None:
        super().__init__(expires, status_code, error)

        if data is not None:
            self.__set_data(data)
        else:
            self.__members: List[FleetMember] = []

    def __set_data(self, data: List[Dict[str, Any]]) -> None:
        self.__members = []
        for member in data:
            logger.debug("Adding FleetMember with data[%s]", member)
            self.__members.append(FleetMember(member))

    def fleet_members(self) -> List[FleetMember]:
        return self.__members


class EveFleet(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str],
                 is_free_move: Optional[bool], is_registered: Optional[bool],
                 is_voice_enabled: Optional[bool], motd: Optional[str]) -> None:
        super(EveFleet, self).__init__(expires, status_code, error)
        self.__is_free_move: bool = is_free_move
        self.__is_registered: bool = is_registered
        self.__is_voice_enabled: bool = is_voice_enabled
        self.__motd: str = motd

    def get_motd(self) -> str:
        return self.__motd

    def get_freemove(self) -> bool:
        return self.__is_free_move

    def get_registered(self) -> bool:
        return self.__is_registered

    def get_voice_enabled(self) -> bool:
        return self.__is_voice_enabled


class EveFleetWings(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str],
                 wings: Optional[List[EveFleetWing]]) -> None:
        super(EveFleetWings, self).__init__(expires, status_code, error)
        self.__wings: List[EveFleetWing] = wings

    def wings(self) -> List[EveFleetWing]:
        return self.__wings


class WingCreated(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str], wing_id: int = None) -> None:
        super(WingCreated, self).__init__(expires, status_code, error)
        self.__wingID: int = wing_id

    def wing_id(self) -> int:
        return self.__wingID


class SquadCreated(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: Optional[str], wing_id: int = None,
                 squad_id: int = None) -> None:
        super(SquadCreated, self).__init__(expires, status_code, error)
        self.__wingID: int = wing_id
        self.__squadID: int = squad_id

    def wing_id(self) -> int:
        # type: () -> int
        return self.__wingID

    def squad_id(self) -> int:
        # type: () -> int
        return self.__squadID
