from typing import Dict, Any, List
from  datetime import datetime
class FleetSettings(object):
    def __init__(self, is_free_move: bool, motd: str) -> None:
        # type: (bool, str) -> None
        self.__is_free_move: bool = is_free_move
        self.__motd: str = motd

    def get_esi_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if self.__is_free_move is not None:
            data['is_free_move'] = self.__is_free_move
        if self.__motd is not None:
            data['motd'] = self.__motd
        return data


class EveFleetSquad(object):
    def __init__(self, squadID: int, squadName: str) -> None:
        # type: (int, str) -> None
        self.__squadID: int = squadID
        self.__squadName: str = squadName

    def id(self) -> int:
        # type: () -> int
        return self.__squadID

    def name(self) -> str:
        # type: () -> str
        return self.__squadName


class EveFleetWing(object):
    def __init__(self, wingID: int, wingName: str, squads: List[EveFleetSquad]):
        # type: (int, str, List[EveFleetSquad]) -> None
        self.__id: int = wingID
        self.__name: str = wingName
        self.__squads: List[EveFleetSquad] = squads

    def squads(self) -> List[EveFleetSquad]:
        # type: () -> List[EveFleetSquad]
        return self.__squads

    def name(self) -> str:
        # type: () -> str
        return self.__name

    def id(self) -> int:
        # type: () -> int
        return self.__id


class FleetMember(object):
    def __init__(self, member: Dict[str, Any]) -> None:
        self._data = member
        self._data['join_time'] = self._data['join_time'].v

    def characterID(self) -> int:
        # type: () -> int
        return self._data['character_id']

    def joinDateTime(self) -> datetime:
        # type: () -> datetime
        return self._data['join_time']

    def role(self) -> str:
        # type: () -> str
        return self._data['role']

    def roleName(self) -> str:
        # type: () -> str
        return self._data['role_name']

    def shipTypeID(self) -> int:
        # type: () -> int
        return self._data['ship_type_id']

    def solarSystem(self) -> int:
        # type: () -> int
        return self._data['solar_system_id']

    def squadID(self) -> int:
        # type: () -> int
        return self._data['squad_id']

    def stationID(self) -> int:
        # type: () -> int
        return self._data['station_id']

    def takesFleetWarp(self) -> bool:
        # type: () -> boolean
        return self._data['takes_fleet_warp']

    def wingID(self) -> int:
        # type: () -> int
        return self.__wing_id
