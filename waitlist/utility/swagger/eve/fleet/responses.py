from waitlist.utility.swagger.eve import ESIResponse
import dateutil

class FleetMember(object):
    def __init__(self, member):
        # type: (FleetMember, dict(str, Any)) -> None
        self._data = member
        self._data['join_time'] = dateutil.parser.parse(self.__data['join_time'])
    
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
    
class EveFleetMembers(ESIResponse):
    def __init__(self, expires, status_code, error, data):
        # type: (datetime, int, str, List[dict(str, Any)]) -> None
        super(ESIResponse).__init__(expires, status_code, error)

        if data is not None:
            self.__setData(data)
        else:
            self.__members = []
        

    def __setData(self, data):
        # type: (List[dict(str, Any)]) -> None
        self.__members = []
        for member in data:
            self.__members.append(FleetMember(member))

    def FleetMember(self):
        # type: () -> List[FleetMember]
        return self.__members

class EveFleet(ESIResponse):
    def __init__(self, expires, status_code, error, is_free_move, is_registered, is_voice_enabled, motd):
        # type: (datetime, boolean, boolean, boolean, str)
        super(ESIResponse).__init__(expires, status_code, error)
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
        self.__wings = wings
        super(ESIResponse).__init__(expires, status_code, error)

    def wings(self):
        # type: () -> List[EveFleetWing]
        return self.__wings

class WingCreated(ESIResponse):
    def __init__(self, expires, status_code, error, wingID):
        # type: (datetime, int, str, int) -> None
        self.__wingID = wingID
        super(ESIResponse).__init__(expires, status_code, error)
    
    def wingID(self):
        # type: () -> int
        return self.__wingID

class SquadCreated(ESIResponse):
    def __init__(self,expires, status_code, error, wingID, squadID):
        # type: (datetime, int, str, int, int) -> None
        self.__wingID = wingID
        self.__squadID = squadID
        super(ESIResponse).__init__(expires, status_code, error)
    
    def wingID(self):
        # type: () -> int
        return self.__wingID
    
    def squadID(self):
        # type: () -> int
        return self.__squadID