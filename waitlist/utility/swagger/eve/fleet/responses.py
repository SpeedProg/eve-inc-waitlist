from waitlist.utility.swagger.eve import ESIResponse
from waitlist.utility.swagger.eve.fleet.models import FleetMember, EveFleetWing
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class EveFleetMembers(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: str, data: List[Dict(str, Any)]) -> None:
        # type: (datetime, int, str, List[dict(str, Any)]) -> None
        super(EveFleetMembers, self).__init__(expires, status_code, error)

        if data is not None:
            self.__setData(data)
        else:
            self.__members: List[FleetMember] = []

    def __setData(self, data: List[Dict(str, Any)]) -> None:
        # type: (List[dict(str, Any)]) -> None
        self.__members = []
        for member in data:
            logger.debug("Adding FleetMember with data[%s]", member)
            self.__members.append(FleetMember(member))

    def FleetMember(self) -> List[FleetMember]:
        # type: () -> List[FleetMember]
        return self.__members


class EveFleet(ESIResponse):
    def __init__(self, expires: datetime, status_code: str, error: str,
                 is_free_move: bool, is_registered: bool,
                 is_voice_enabled: bool, motd: str) -> None:
        # type: (datetime, boolean, boolean, boolean, str)
        super(EveFleet, self).__init__(expires, status_code, error)
        self.__is_free_move: bool = is_free_move
        self.__is_registered: bool = is_registered
        self.__is_voice_enabled: bool = is_voice_enabled
        self.__motd: str = motd

    def get_MOTD(self) -> str:
        # type: () -> str
        return self.__motd

    def get_freemove(self) -> bool:
        # type: () -> boolean
        return self.__is_free_move

    def get_registered(self) -> bool:
        # type: () -> boolean
        return self.__is_registered

    def get_voice_enabled(self) -> bool:
        # type: () -> boolean
        return self.__is_voice_enabled


class EveFleetWings(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: str,
                 wings: List[EveFleetWing]):
        # type: (datetime, boolean, boolean, str, List[EveFleetWing]) -> None
        super(EveFleetWings, self).__init__(expires, status_code, error)
        self.__wings: List[EveFleetWing] = wings

    def wings(self) -> List[EveFleetWings]:
        # type: () -> List[EveFleetWing]
        return self.__wings


class WingCreated(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: str, wingID: int) -> None:
        # type: (datetime, int, str, int) -> None
        super(WingCreated, self).__init__(expires, status_code, error)
        self.__wingID: int = wingID

    def wingID(self) -> int:
        # type: () -> int
        return self.__wingID


class SquadCreated(ESIResponse):
    def __init__(self, expires: datetime, status_code: int, error: str, wingID: int, squadID: int) -> None:
        # type: (datetime, int, str, int, int) -> None
        super(SquadCreated, self).__init__(expires, status_code, error)
        self.__wingID: int = wingID
        self.__squadID: int = squadID

    def wingID(self) -> int:
        # type: () -> int
        return self.__wingID

    def squadID(self) -> int:
        # type: () -> int
        return self.__squadID
