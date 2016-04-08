from waitlist.storage.database import Constellation, SolarSystem, Station,\
    InvType, Account, Character, Ban
from waitlist import db
import logging
from waitlist.data.eve_xml_api import get_character_id_from_name,\
    get_affiliation

logger = logging.getLogger(__name__)



def get_constellation(name):
    return db.session.query(Constellation).filter(Constellation.constellationName == name).first()

def get_system(name):
    return db.session.query(SolarSystem).filter(SolarSystem.solarSystemName == name).first()

def get_station(name):
    return db.session.query(Station).filter(Station.stationName == name).first()

def get_item_id(name):
    logger.debug("Getting id for item %s", name)
    item = db.session.query(InvType).filter(InvType.typeName == name).first()
    if item == None:
        return -1
    return item.typeID

# load an account by its id
def get_account_from_db(int_id):
    return db.session.query(Account).filter(Account.id == int_id).first()

# load a character by its id
def get_char_from_db(int_id):
    return db.session.query(Character).filter(Character.id == int_id).first()

def create_new_character(eve_id, char_name):
    char = Character()
    char.id = eve_id
    char.eve_name = char_name
    char.newbro = True
    db.session.add(char)
    db.session.commit()
    return char

def get_character_by_id_and_name(eve_id, eve_name):
    char = get_char_from_db(eve_id);
    if char == None:
        logger.info("No character found for id %d", eve_id)
        # create a new char
        char = create_new_character(eve_id, eve_name)

    return char

def is_charid_banned(eve_id):
    if eve_id == 0: # this stands for no id in the eve api (for example no alliance)
        return False
    return db.session.query(Ban).filter(Ban.id == eve_id).count() == 1

def get_character_by_name(eve_name):
    eve_id = get_character_id_from_name(eve_name)
    if eve_id == 0:
        return None
    return get_character_by_id_and_name(eve_id, eve_name)

def is_char_banned(char):
    reason = "Character"
    is_banned = char.banned
    if not is_banned:
        corp_id, alli_id = get_affiliation(char.get_eve_id())
        if (is_charid_banned(corp_id)):
            reason = "Corporation"
            is_banned = True
        elif is_charid_banned(alli_id):
            reason = "Alliance"
            is_banned = True

    return is_banned, reason