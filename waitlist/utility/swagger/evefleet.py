from waitlist.utility.swagger import api, header_to_datetime, ESIResponse
from waitlist.utility.config import crest_return_url, crest_client_id,\
    crest_client_secret
from esipy.client import EsiClient
from flask_login import current_user
from esipy.security import EsiSecurity
from datetime import datetime

def get_esi_client():
    # type: () -> EsiClient
    security = EsiSecurity(
        api,
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': current_user.ssoToken.access_token,
        'expires_in': (current_user.ssoToken.access_token_expires - datetime.utcnow()).total_seconds(),
        'refresh_token': current_user.ssoToken.refresh_token
    })
    client = EsiClient(security)
    return client

def get_expire_time(response):
    # type: (Any) -> datetime
    cacheTime = header_to_datetime(response.header['Expires'][0])
    return header_to_datetime(cacheTime)

def get_members(fleetID):
    # type: (int) -> dict(str, Any)
    client = get_esi_client()
    response = client.request(api.op['get_fleets_fleet_id_members'](fleet_id=fleetID))

    return {'expires': get_expire_time(response), 'data': response.data, 'response': response}

def invite_member(fleetID, characterID, role, squadID, wingID):
    # type: (int, int, str, int, int) -> dict(str, Any)
    client = get_esi_client()
    invite = {};
    invite['character_id'] = characterID
    invite['role'] = role
    if squadID is not None:
        invite['squad_id'] = squadID
    if wingID is not None:
        invite['wing_id'] = wingID
    response = client.request(api.op['post_fleets_fleet_id_members_invitation'](fleet_id=fleetID, invitation=invite))

    return {'expires': get_expire_time(response), 'data': response.data, 'response': response}

def get_fleet(fleetID):
    # type: (int) -> dict(str, Any)
    '''
    Get fleet information
    get_fleets_fleet_id_ok {
        is_free_move (boolean):
        
        Is free-move enabled ,
        is_registered (boolean):
        
        Does the fleet have an active fleet advertisement ,
        is_voice_enabled (boolean):
        
        Is EVE Voice enabled ,
        motd (string):
        
        Fleet MOTD in CCP flavoured HTML
    }
    '''
    client = get_esi_client()
    response = client.request(api.op['get_fleets_fleet_id'](fleet_id=fleetID))

    return get_fleet_from_response(response)

def get_fleet_from_response(response):
    # type: () -> EveFleet
    if (response.status_code == 200):
        return EveFleet(get_expire_time(response), response.status_code, None,
                         response.data['is_free_move'], response.data['is_registered'],
                         response.data['is_voice_enabled'], response.data['motd'])
    return EveFleet(get_expire_time(response), response.status_code, response.data['error'],
                    None, None,
                    None, None
                    )

class EveFleet(ESIResponse):
    def __init__(self, expires, status_code, error, is_free_move, is_registered, is_voice_enabled, motd):
        # type: (datetime, boolean, boolean, boolean, str)
        self.__is_free_move = is_free_move
        self.__is_registered = is_registered
        self.__is_voice_enabled = is_voice_enabled
        self.__motd = motd
        super(ESIResponse).__init__(expires, status_code, error)
    
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

def put_fleet(fleetID, is_free_move, motd):
    # type: (int, boolean, str) -> ESIResponse
    settings = FleetSettings(is_free_move, motd)
    client = get_esi_client()
    
    response = client.request(api.op['put_fleets_fleet_id_new_settings'](fleet_id=fleetID, new_settings=settings.get_esi_data()))
    if response.status_code == 204:
        return ESIResponse(get_expire_time(response), response.status_code, None)
    return ESIResponse(get_expire_time(response), response.status_code, response.data['error'])

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

class EveFleetWings(ESIResponse):
    def __init__(self, expires, status_code, error, wings):
        # type: (datetime, boolean, boolean, str, List[EveFleetWing]) -> None
        self.__wings = wings
        super(ESIResponse).__init__(expires, status_code, error)

    def wings(self):
        # type: () -> List[EveFleetWing]
        return self.__wings

def get_wings(fleetID):
    # type: (int) -> EveFleetWings
    client = get_esi_client()
    response = client.request(api.op['get_fleets_fleet_id_wings'](fleet_id=fleetID))
    if response.status_code == 200:
        wings = []
        for wing in response.data:
            wingID = wing['id']
            wingName = wing['name']
            squads = []
            for squad in wing['squads']:
                squad = EveFleetSquad(squad['id'], squad['name'])
                squads.append(squad)
            fleetWing = EveFleetWing(wingID, wingName, squads)
            wings.append(fleetWing)
        
        fleetWings = EveFleetWings(get_expire_time(response), response.status_code, None, wings)
        return fleetWings

    return EveFleetWings(get_expire_time(response), response.status_code, response.data['error'], None)

class WingCreated(ESIResponse):
    def __init__(self, expires, status_code, error, wingID):
        # type: (datetime, int, str, int) -> None
        self.__wingID = wingID
        super(ESIResponse).__init__(expires, status_code, error)
    
    def wingID(self):
        # type: () -> int
        return self.__wingID

def create_wing(fleetID):
    # type: (int) -> WingCreated
    client = get_esi_client()
    response = client.request(api.op['post_fleets_fleet_id_wings'](fleet_id=fleetID))
    if response.status_code == 201:
        return WingCreated(get_expire_time(response), response.status_code, None,
                           response.data['wing_id']
                           )
    return WingCreated(get_expire_time(response), response.status_code, response.data['error'])

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

class EveFleetEndpoint(object):
    def __init__(self, fleetID):
        # type: (int) -> None
        self.__fleetID = fleetID
    
    def get_fleet_settings(self):
        # type: () -> EveFleet
        return get_fleet(self.__fleetID)
    
    def set_fleet_settings(self, is_free_move, motd):
        # type: (boolean, str) -> ESIResponse
        return put_fleet(self.__fleetID, is_free_move, motd)
    
    def get_wings(self):
        # type: () -> VarType(EveFleetWings, ESIResponse)
        return get_wings(self.__fleetID)
    
    def create_wing(self):
        # type: () -> WingCreated
        return create_wing(self.__fleetID)
    
    def set_wing_name(self, wingID, name):
        # type: (int, str) -> ESIResponse
        client = get_esi_client()
        data = {'name': name}
        response = client.request(api.op['put_fleets_fleet_id_wings_wing_id'](fleet_id=self.__fleetID, wing_id=wingID, naming=data))
        
        if response.status_code == 204:
            return ESIResponse(get_expire_time(response), response.status_code, None)

        return ESIResponse(get_expire_time(response), response.status_code, response.data['error'])

    def create_squad(self, wingID):
        # type: (int) -> SquadCreated
        client = get_esi_client()
        response = client.request(api.op['post_fleets_fleet_id_wings_wing_id_squads'](fleet_id=self.__fleetID, wing_id=wingID))
        if response.status_code == 201:
            return SquadCreated(get_expire_time(response), response.status_code, None,
                                wingID, response.data['squad_id']
                                )
        return SquadCreated(get_expire_time(response), response.status_code, None, None, None)
    
    def set_squad_name(self, squadID, name):
        # type: (int, str) -> ESIResponse
        client = get_esi_client()
        response = client.request(api.op['put_fleets_fleet_id_squads_squad_id'](fleet_id=self.__fleetID, squad_id=squadID))
        if response.status_code == 204:
            return ESIResponse(get_expire_time(response), response.status_code, None)
        return ESIResponse(get_expire_time(response), response.status_code, response.data['error'])
    
    def invite(self, characterID, role, squadID, wingID):
        # type: (int, str, int, int) -> dict(str, Any)
        return invite_member(self.__fleetID, characterID, role, squadID, wingID)