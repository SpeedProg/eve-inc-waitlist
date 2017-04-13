from typing import Optional, Tuple

from utility import outgate
from waitlist.storage.database import Constellation, SolarSystem, Station,\
    InvType, Account, Character, Ban, Whitelist
from waitlist import db
import logging

logger = logging.getLogger(__name__)


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
        return -1
    return item.typeID


# load an account by its id
def get_account_from_db(int_id: int) -> Account:
    return db.session.query(Account).filter(Account.id == int_id).first()


# load a character by its id
def get_char_from_db(int_id: int) -> Character:
    return db.session.query(Character).filter(Character.id == int_id).first()


def create_new_character(eve_id: int, char_name: str) -> Character:
    char = Character()
    char.id = eve_id
    char.eve_name = char_name
    char.newbro = True
    db.session.add(char)
    db.session.commit()
    return char


def get_character_by_id_and_name(eve_id: int, eve_name: str) -> Character:
    char = get_char_from_db(eve_id)
    if char is None:
        logger.info("No character found for id %d", eve_id)
        # create a new char
        char = create_new_character(eve_id, eve_name)

    return char


def is_charid_banned(character_id: int) -> bool:
    if character_id == 0:  # this stands for no id in the eve api (for example no alliance)
        return False
    return db.session.query(Ban).filter(Ban.id == character_id).count() == 1


def is_charid_whitelisted(character_id: int) -> bool:
    if character_id == 0:
        return False
    return db.session.query(Whitelist).filter(Whitelist.characterID == character_id).count() == 1


def get_character_by_name(eve_name: str) -> Optional[Character]:
    eve_info = outgate.character.get_info_by_name(eve_name)
    if eve_info is None:
        return None
    return get_character_by_id_and_name(eve_info.id, eve_name)


def is_char_banned(char: Character) -> Tuple[bool, str]:
    try:
        corp_id, alli_id = outgate.character.get_affiliations(char.get_eve_id())
        # if he is on whitelist let him pass
        
        char_banned = char.banned
        corp_banned = is_charid_banned(corp_id)
        alli_banned = is_charid_banned(alli_id)
        
        if is_charid_whitelisted(char.get_eve_id()):
            return False, ""
        
        if char_banned:
            return True, "Character"
        
        if is_charid_whitelisted(corp_id):
                return False, ""
        
        if corp_banned:
            return True, "Corporation"
        
        if is_charid_whitelisted(alli_id):
                return False, ""
        
        if alli_banned:
            return True, "Alliance"
        
        return False, ""
    except Exception:
        logger.error("Failed to check if %d was banned", char.get_eve_id(), exc_info=1)
        return False, ""
