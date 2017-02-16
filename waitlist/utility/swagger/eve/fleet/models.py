from typing import Dict, Any, List
from datetime import datetime


class FleetSettings(object):
    def __init__(self, is_free_move: bool, motd: str) -> None:
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
    def __init__(self, squad_id: int, squad_name: str) -> None:
        self.__squadID: int = squad_id
        self.__squadName: str = squad_name

    def id(self) -> int:
        return self.__squadID

    def name(self) -> str:
        return self.__squadName


class EveFleetWing(object):
    def __init__(self, wing_id: int, wing_name: str, squads: List[EveFleetSquad]) -> None:
        self.__id: int = wing_id
        self.__name: str = wing_name
        self.__squads: List[EveFleetSquad] = squads

    def squads(self) -> List[EveFleetSquad]:
        return self.__squads

    def name(self) -> str:
        return self.__name

    def id(self) -> int:
        return self.__id


class FleetMember(object):
    def __init__(self, member: Dict[str, Any]) -> None:
        self._data = member
        self._data['join_time'] = self._data['join_time'].v

    def character_id(self) -> int:
        return self._data['character_id']

    def join_datetime(self) -> datetime:
        return self._data['join_time']

    def role(self) -> str:
        return self._data['role']

    def role_name(self) -> str:
        return self._data['role_name']

    def ship_type_id(self) -> int:
        return self._data['ship_type_id']

    def solar_system(self) -> int:
        return self._data['solar_system_id']

    def squad_id(self) -> int:
        return self._data['squad_id']

    def station_id(self) -> int:
        return self._data['station_id']

    def takes_fleet_warp(self) -> bool:
        return self._data['takes_fleet_warp']

    def wing_id(self) -> int:
        return self._data['wing_id']

    @property
    def data(self):
        return self._data
