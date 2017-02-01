from waitlist.utility.swagger import api, header_to_datetime
from waitlist.utility.swagger.eve import get_esi_client, ESIResponse,\
    get_expire_time
from waitlist.utility.swagger.eve.fleet.responses import EveFleet, EveFleetWings,\
    WingCreated, EveFleetMembers, SquadCreated
from waitlist.utility.swagger.eve.fleet.models import EveFleetWing,\
    EveFleetSquad, FleetSettings
import logging
from esipy.client import EsiClient
from typing import Any

logger = logging.getLogger(__name__)


class EveFleetEndpoint(object):
    def __init__(self, fleetID: int, client: EsiClient = None) -> None:
        # type: (int, EsiClient) -> None
        self.__fleetID: int = fleetID
        self.__client: EsiClient = get_esi_client() if client is None else client

    def get_member(self) -> EveFleetMembers:
        response = self.__client.request(api.op['get_fleets_fleet_id_members'](fleet_id=self.__fleetID))
        logger.debug("Got ESI Response with status[%d]", response.status)
        if response.status == 200:
            return EveFleetMembers(get_expire_time(response),
                                   response.status,
                                   None, response.data)
        return EveFleetMembers(get_expire_time(response), response.status,
                               response.data['error'], None)

    def get_fleet_settings(self) -> EveFleet:
        # type: () -> EveFleet
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
        response = self.__client.request(api.op['get_fleets_fleet_id'](fleet_id=self.__fleetID))
        if (response.status == 200):
            return EveFleet(get_expire_time(response), response.status,
                            None,
                            response.data['is_free_move'],
                            response.data['is_registered'],
                            response.data['is_voice_enabled'],
                            response.data['motd'])
        return EveFleet(get_expire_time(response), response.status,
                        response.data['error'],
                        None, None,
                        None, None
                        )

    def set_fleet_settings(self, is_free_move: bool, motd: str) -> ESIResponse:
        # type: (boolean, str) -> ESIResponse
        settings = FleetSettings(is_free_move, motd)

        response = self.__client.request(api.op['put_fleets_fleet_id'](
            fleet_id=self.__fleetID,
            new_settings=settings.get_esi_data()
            ))
        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)
        return ESIResponse(get_expire_time(response), response.status,
                           response.data['error'])

    def get_wings(self) -> EveFleetWings:
        # type: () -> EveFleetWings
        client = get_esi_client()
        response = client.request(api.op['get_fleets_fleet_id_wings'](fleet_id=self.__fleetID))
        if response.status == 200:
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

            return EveFleetWings(get_expire_time(response),
                                 response.status,
                                 None, wings)
        return EveFleetWings(get_expire_time(response), response.status,
                             response.data['error'], None)

    def create_wing(self) -> WingCreated:
        # type: () -> WingCreated
        response = self.__client.request(api.op['post_fleets_fleet_id_wings'](fleet_id=self.__fleetID))
        if response.status == 201:
            return WingCreated(get_expire_time(response), response.status,
                               None,
                               response.data['wing_id']
                               )
        return WingCreated(get_expire_time(response), response.status,
                           response.data['error'])

    def set_wing_name(self, wingID: int, name: str) -> ESIResponse:
        # type: (int, str) -> ESIResponse
        data = {'name': name}
        response = self.__client.request(
            api.op['put_fleets_fleet_id_wings_wing_id'](
                fleet_id=self.__fleetID, wing_id=wingID, naming=data
            )
        )

        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)

        return ESIResponse(get_expire_time(response), response.status,
                           response.data['error'])

    def create_squad(self, wingID: int) -> SquadCreated:
        # type: (int) -> SquadCreated
        response = self.__client.request(api.op['post_fleets_fleet_id_wings_wing_id_squads'](fleet_id=self.__fleetID, wing_id=wingID))
        if response.status == 201:
            return SquadCreated(get_expire_time(response),
                                response.status,
                                None,
                                wingID, response.data['squad_id']
                                )

        return SquadCreated(get_expire_time(response), response.status,
                            None, None, None)

    def set_squad_name(self, squadID: int, name: str) -> ESIResponse:
        # type: (int, str) -> ESIResponse
        response = self.__client.request(api.op['put_fleets_fleet_id_squads_squad_id'](
            fleet_id=self.__fleetID, squad_id=squadID, naming={'name': name}))

        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)
        return ESIResponse(get_expire_time(response), response.status,
                           response.data['error'])

    def invite(self, characterID: int, role: str, squadID: str, wingID: int) -> ESIResponse:
        # type: (int, str, int, int) -> dict(str, Any)
        '''
        'fleet_commander', 'wing_commander', 'squad_commander', 'squad_member'
        '''
        invite: Dict(str, Any) = {}
        invite['character_id'] = characterID
        invite['role'] = role
        if squadID is not None:
            invite['squad_id'] = squadID
        if wingID is not None:
            invite['wing_id'] = wingID
        response = self.__client.request(api.op['post_fleets_fleet_id_members'](
            fleet_id=self.__fleetID, invitation=invite))

        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)
        return ESIResponse(get_expire_time(response), response.status,
                           response.data['error'])
