from dateutil.parser import parse


class FleetSettings(object):
    def __init__(self, is_free_move, motd):
        # type: (boolean, str) -> None
        self.__is_free_move = is_free_move
        self.__motd = motd

    def get_esi_data(self):
        data = {}
        if self.__is_free_move is not None:
            data['is_free_move'] = self.__is_free_move
        if self.__motd is not None:
            data['motd'] = self.__motd
        return data


class EveFleetSquad(object):
    def __init__(self, squadID, squadName):
        # type: (int, str) -> None
        self.__squadID = squadID
        self.__squadName = squadName

    def id(self):
        # type: () -> int
        return self.__squadID

    def name(self):
        # type: () -> str
        return self.__squadName


class EveFleetWing(object):
    def __init__(self, wingID, wingName, squads):
        # type: (int, str, List[EveFleetSquad]) -> None
        self.__id = wingID
        self.__name = wingName
        self.__squads = squads

    def squads(self):
        # type: () -> List[EveFleetSquad]
        return self.__squads

    def name(self):
        # type: () -> str
        return self.__name

    def id(self):
        # type: () -> int
        return self.__id


class FleetMember(object):
    def __init__(self, member):
        # type: (FleetMember, dict(str, Any)) -> None
        self._data = member
        self._data['join_time'] = self._data['join_time'].v

    def characterID(self):
        # type: () -> int
        return self._data['character_id']

    def joinDateTime(self):
        # type: () -> datetime
        return self._data['join_time']

    def role(self):
        # type: () -> str
        return self._data['role']

    def roleName(self):
        # type: () -> str
        return self._data['role_name']

    def shipTypeID(self):
        # type: () -> int
        return self._data['ship_type_id']

    def solarSystem(self):
        # type: () -> int
        return self._data['solar_system_id']

    def squadID(self):
        # type: () -> int
        return self._data['squad_id']

    def stationID(self):
        # type: () -> int
        return self._data['station_id']

    def takesFleetWarp(self):
        # type: () -> boolean
        return self._data['takes_fleet_warp']

    def wingID(self):
        # type: () -> int
        return self.__wing_id
