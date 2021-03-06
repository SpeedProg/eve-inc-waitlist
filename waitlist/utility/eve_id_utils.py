from typing import Optional, Tuple

from esipy import EsiClient

from waitlist.utility import outgate
from waitlist.utility.config import banned_by_default
from waitlist.utility.sde import add_type_by_id_to_database
from waitlist.storage.database import Constellation, SolarSystem, Station,\
    InvType, Account, Character, Ban, Whitelist, CharacterTypes
from waitlist.base import db
import logging

from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve import get_esi_client
from waitlist.utility.swagger.eve.search import SearchEndpoint, SearchResponse
from threading import Lock
from waitlist.utility.outgate.exceptions import ApiException, ESIException
from waitlist.utility.outgate import character, corporation, alliance

logger = logging.getLogger(__name__)

"""
Lock for checking existance of a character and creating it
"""
character_check_lock: Lock = Lock()


def get_constellation(name: str) -> Constellation:
    return db.session.query(Constellation).filter(Constellation.constellationName == name).first()


def get_system(name: str) -> SolarSystem:
    return db.session.query(SolarSystem).filter(SolarSystem.solarSystemName == name).first()


def get_station(name: str) -> Station:
    return db.session.query(Station).filter(Station.stationName == name).first()


def get_item_id(name: str) -> int:
    logger.debug("Getting id for item %s", name)
    item = db.session.query(InvType).filter(InvType.typeName == name).first()
    if item is None:
        item_data = get_item_data_from_api(name)
        if item_data is None:
            return -1

        # add the type to db
        current_type: InvType = db.session.query(InvType).get(item_data.type_id)
        # Was it only renamed?
        if current_type is not None:
            item = InvType(typeID=item_data.type_id, groupID=item_data.group_id,
                           typeName=item_data.name, description=item_data.description,
                          marketGroupID=getattr(item_data, 'market_group_id', None))

            db.session.merge(item)
            db.session.commit()
            logger.info(f'Updated {item}')
        else:
            item = add_type_by_id_to_database(item_data.type_id)
            db.session.commit()
            logger.info(f'Added new {item}')

    return item.typeID


def get_item_data_from_api(name: str) -> Optional[any]:
    """Tries to get api data of an item with this name from Search API"""
    search_endpoint = SearchEndpoint()
    search_response: SearchResponse = search_endpoint.public_search(name, ['inventory_type'], True)
    result_ids = search_response.inventory_type_ids()
    if result_ids is None or len(result_ids) < 1:
        return None

    esi_client: EsiClient = get_esi_client(None, True)
    api = get_api()

    for result_id in result_ids:
        type_result = esi_client.request(api.op['get_universe_types_type_id'](type_id=result_id))
        if type_result.data.name == name:
            return type_result.data

    return None


# load an account by its id
def get_account_from_db(int_id: int) -> Account:
    return db.session.query(Account).filter(Account.id == int_id).first()


# load a character by its id
def get_char_from_db(int_id: int) -> Character:
    return db.session.query(Character).get(int_id)


def create_new_character(eve_id: int, char_name: str) -> Character:
    char = Character()
    char.id = eve_id
    char.eve_name = char_name
    char.is_new = True
    db.session.add(char)
    db.session.commit()
    return char


def get_character_by_id_and_name(eve_id: int, eve_name: str) -> Character:
    with character_check_lock:
        char = get_char_from_db(eve_id)
        if char is None:
            logger.info("No character found for id %d", eve_id)
            # create a new char
            char = create_new_character(eve_id, eve_name)

        return char


def get_character_by_id(eve_character_id: int) -> Character:
    """
    :throws ApiException if there was a problem contacting the api
    """
    with character_check_lock:
        character: Character = get_char_from_db(eve_character_id)
        if character is None:
            logger.info("No character found in database for id %d", eve_character_id)
            char_info = outgate.character.get_info(eve_character_id)
            character = create_new_character(eve_character_id, char_info.characterName)

        return character


def is_charid_banned(character_id: int) -> bool:
    if character_id == 0:  # this stands for no id in the eve api (for example no alliance)
        return False
    return db.session.query(Ban).filter(Ban.id == character_id).count() == 1


def is_charid_whitelisted(character_id: int) -> bool:
    if character_id == 0:
        return False
    return db.session.query(Whitelist).filter(Whitelist.characterID == character_id).count() == 1


def get_character_by_name(eve_name: str) -> Optional[Character]:
    try:
        eve_info = outgate.character.get_info_by_name(eve_name)
        if eve_info is None:
            return None
        return get_character_by_id_and_name(eve_info.id, eve_name)
    except ApiException:
        return None

def get_character_type_by_id(char_id: int) -> Tuple[CharacterTypes,int]:
    """
    :returns the character type and how many potential ESI error where created
    """
    try:
        char_info: APICacheCharacterInfo = character.get_info(char_id)
        return CharacterTypes.character, 0
    except ESIException:
        pass  # no such char
    try:
        corp_info: APICacheCorporationInfo = corporation.get_info(char_id)
        return CharacterTypes.corporation, 1
    except ESIException:
        pass  # no such corp
    all_info: APICacheAllianceInfo = alliance.get_info(char_id)
    return CharacterTypes.alliance, 2


def get_char_corp_all_name_by_id_and_type(char_id: int, char_type: CharacterTypes) -> str:
    if char_type == CharacterTypes.character:
        return character.get_info(char_id).characterName
    if char_type == CharacterTypes.corporation:
        return corporation.get_info(char_id).name
    if char_type == CharacterTypes.alliance:
        return alliance.get_info(char_id).allianceName
    raise ValueError('Unknown Character type supplied')


def is_char_banned(char: Character) -> Tuple[bool, str]:
    try:
        if is_charid_whitelisted(char.get_eve_id()):
            return False, ""

        if char.banned:
            return True, "Character"

        char_info = outgate.character.get_info(char.get_eve_id())

        if is_charid_whitelisted(char_info.corporationID):
            return False, ""

        if is_charid_banned(char_info.corporationID):
            return True, "Corporation"

        if char_info.allianceID is not None:
            if is_charid_whitelisted(char_info.allianceID):
                return False, ""

            if is_charid_banned(char_info.allianceID):
                return True, "Alliance"

        if banned_by_default:
            return True, "Everyone Banned by default"
        else:
            return False, ""
    except ApiException as e:
        logger.info("Failed to check if %d was banned, because of Api error, code=%d msg=%s",
                    char.get_eve_id(), e.code, e.msg)
        return False, ""
    except Exception:
        logger.error("Failed to check if %d was banned", char.get_eve_id(), exc_info=1)
        return False, ""
