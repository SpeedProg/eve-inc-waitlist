from pyswagger import App

from waitlist.utility.swagger.eve import get_esi_client, ESIResponse, \
    get_expire_time, make_error_response
from waitlist.utility.swagger.eve.fleet.responses import EveFleet, EveFleetWings, \
    WingCreated, EveFleetMembers, SquadCreated
from waitlist.utility.swagger.eve.fleet.models import EveFleetWing, \
    EveFleetSquad, FleetSettings
import logging
from esipy.client import EsiClient
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EveFleetEndpoint(object):
    def __init__(self, fleet_id: int, client: EsiClient = None) -> None:
        self.__fleetID: int = fleet_id
        if client is None:
            self.__client: EsiClient = get_esi_client('v1')
            self.__api: App = self.__client.security.app
        else:
            self.__client: EsiClient = client
            self.__api: App = self.__client.security.app

    def get_member(self) -> EveFleetMembers:
        response = self.__client.request(self.__api.op['get_fleets_fleet_id_members'](fleet_id=self.__fleetID))
        logger.debug("Got ESI Response with status[%d]", response.status)
        if response.status == 200:
            return EveFleetMembers(get_expire_time(response),
                                   response.status,
                                   None, response.data)
        return make_error_response(response)

    def get_fleet_settings(self) -> EveFleet:
        # type: () -> EveFleet
        """
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
        """
        response = self.__client.request(self.__api.op['get_fleets_fleet_id'](fleet_id=self.__fleetID))
        if response.status == 200:
            return EveFleet(get_expire_time(response), response.status,
                            None,
                            response.data['is_free_move'],
                            response.data['is_registered'],
                            response.data['is_voice_enabled'],
                            response.data['motd'])
        return make_error_response(response)

    def set_fleet_settings(self, is_free_move: bool, motd: str) -> ESIResponse:
        settings = FleetSettings(is_free_move, motd)

        response = self.__client.request(self.__api.op['put_fleets_fleet_id'](
            fleet_id=self.__fleetID,
            new_settings=settings.get_esi_data()
        ))
        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)

        return make_error_response(response)

    def get_wings(self) -> EveFleetWings:
        response = self.__client.request(self.__api.op['get_fleets_fleet_id_wings'](fleet_id=self.__fleetID))
        if response.status == 200:
            wings = []
            for wing in response.data:
                wing_id = wing['id']
                wing_name = wing['name']
                squads = []
                for squad in wing['squads']:
                    squad = EveFleetSquad(squad['id'], squad['name'])
                    squads.append(squad)
                fleet_wing = EveFleetWing(wing_id, wing_name, squads)
                wings.append(fleet_wing)

            return EveFleetWings(get_expire_time(response),
                                 response.status,
                                 None, wings)
        return make_error_response(response)

    def create_wing(self) -> WingCreated:
        response = self.__client.request(self.__api.op['post_fleets_fleet_id_wings'](fleet_id=self.__fleetID))
        if response.status == 201:
            return WingCreated(get_expire_time(response), response.status,
                               None,
                               response.data['wing_id']
                               )
        return make_error_response(response)

    def set_wing_name(self, wing_id: int, name: str) -> ESIResponse:
        # type: (int, str) -> ESIResponse
        data = {'name': name}
        response = self.__client.request(
            self.__api.op['put_fleets_fleet_id_wings_wing_id'](
                fleet_id=self.__fleetID, wing_id=wing_id, naming=data
            )
        )

        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)

        return make_error_response(response)

    def create_squad(self, wing_id: int) -> SquadCreated:
        response = self.__client.request(self.__api.op['post_fleets_fleet_id_wings_wing_id_squads']
                                         (fleet_id=self.__fleetID, wing_id=wing_id))
        if response.status == 201:
            return SquadCreated(get_expire_time(response),
                                response.status,
                                None,
                                wing_id, response.data['squad_id']
                                )

        return SquadCreated(get_expire_time(response), response.status,
                            None, None, None)

    def set_squad_name(self, squad_id: int, name: str) -> ESIResponse:
        response = self.__client.request(self.__api.op['put_fleets_fleet_id_squads_squad_id'](
            fleet_id=self.__fleetID, squad_id=squad_id, naming={'name': name}))

        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)
        return make_error_response(response)

    def invite(self, character_id: int, role: str, squad_id: int, wing_id: int) -> ESIResponse:
        """
        'fleet_commander', 'wing_commander', 'squad_commander', 'squad_member'
        """
        invite: Dict[str, Any] = {'character_id': character_id, 'role': role}
        if squad_id is not None:
            invite['squad_id'] = squad_id
        if wing_id is not None:
            invite['wing_id'] = wing_id
        response = self.__client.request(self.__api.op['post_fleets_fleet_id_members'](
            fleet_id=self.__fleetID, invitation=invite))

        if response.status == 204:
            return ESIResponse(get_expire_time(response), response.status,
                               None)
        return make_error_response(response)
