from waitlist.utility.swagger.eve import ESIResponse
from waitlist.utility.swagger.eve.fleet.models import FleetMember
import logging

logger = logging.getLogger(__name__)


class EveFleetMembers(ESIResponse):
    def __init__(self, expires, status_code, error, data):
        # type: (datetime, int, str, List[dict(str, Any)]) -> None
        super(EveFleetMembers, self).__init__(expires, status_code, error)

        if data is not None:
            self.__setData(data)
        else:
            self.__members = []

    def __setData(self, data):
        # type: (List[dict(str, Any)]) -> None
        self.__members = []
        for member in data:
            logger.debug("Adding FleetMember with data[%s]", member)
            self.__members.append(FleetMember(member))

    def FleetMember(self):
        # type: () -> List[FleetMember]
        return self.__members


class EveFleet(ESIResponse):
    def __init__(self, expires, status_code, error, is_free_move,
                 is_registered, is_voice_enabled, motd):
        # type: (datetime, boolean, boolean, boolean, str)
        super(EveFleet, self).__init__(expires, status_code, error)
        self.__is_free_move = is_free_move
        self.__is_registered = is_registered
        self.__is_voice_enabled = is_voice_enabled
        self.__motd = motd

    def get_MOTD(self):
        # type: () -> str
        return self.__motd

    def get_freemove(self):
        # type: () -> boolean
        return self.__is_free_move

    def get_registered(self):
        # type: () -> boolean
        return self.__is_registered

    def get_voice_enabled(self):
        # type: () -> boolean
        return self.__is_voice_enabled


class EveFleetWings(ESIResponse):
    def __init__(self, expires, status_code, error, wings):
        # type: (datetime, boolean, boolean, str, List[EveFleetWing]) -> None
        super(EveFleetWings, self).__init__(expires, status_code, error)
        self.__wings = wings

    def wings(self):
        # type: () -> List[EveFleetWing]
        return self.__wings


class WingCreated(ESIResponse):
    def __init__(self, expires, status_code, error, wingID):
        # type: (datetime, int, str, int) -> None
        super(WingCreated, self).__init__(expires, status_code, error)
        self.__wingID = wingID

    def wingID(self):
        # type: () -> int
        return self.__wingID


class SquadCreated(ESIResponse):
    def __init__(self, expires, status_code, error, wingID, squadID):
        # type: (datetime, int, str, int, int) -> None
        super(SquadCreated, self).__init__(expires, status_code, error)
        self.__wingID = wingID
        self.__squadID = squadID

    def wingID(self):
        # type: () -> int
        return self.__wingID

    def squadID(self):
        # type: () -> int
        return self.__squadID
