from typing import Tuple

from waitlist.storage.database import APICacheCharacterID, APICacheCharacterInfo, APICacheCharacterAffiliation
from waitlist import db
from datetime import datetime
import logging
from waitlist.utility.swagger import character_info

logger = logging.getLogger(__name__)


def get_character_id_from_name(name: str) -> int:
    character = db.session.query(APICacheCharacterID).filter(APICacheCharacterID.name == name).first()
    if character is None:
        char_id, char_name = character_info.characterid_from_name(name)
        if char_id is None or char_name is None:
            return 0
        character = APICacheCharacterID()
        character.id = char_id
        character.name = name
        db.session.add(character)
        db.session.commit()
    
    return character.id
        

def get_char_info_for_character(char_id: int) -> APICacheCharacterInfo:
    # check cache first
    char_info = db.session.query(APICacheCharacterInfo).filter(APICacheCharacterInfo.id == char_id).first()

    if char_info is None:
        char_info = APICacheCharacterInfo()
        result, expires = character_info.get_character_info(char_id)
        corp_id = result['corporation_id']
        corp_name = result['corporation_name']
        char_name = result['name']
        char_info.id = char_id
        char_info.corporationID = corp_id
        char_info.corporationName = corp_name
        char_info.characterName = char_name
        char_info.expire = expires
        db.session.add(char_info)
        db.session.commit()
    elif char_info.characterName is None:
        result, _ = character_info.get_character_info(char_id)
        char_info.characterName = result['name']
        db.session.commit()
    else:
        now = datetime.now()
        if char_info.expire is None or char_info.expire < now:
            # expired, update it
            result, expire = character_info.get_character_info(char_id)
            corp_id = result['corporation_id']
            corp_name = result['corporation_name']
            char_name = result['name']
            char_info.corporationID = corp_id
            char_info.corporationName = corp_name
            char_id.characterName = char_name
            char_info.expire = expire
            db.session.commit()
    
    return char_info


def get_affiliation(char_id: int) -> Tuple[int, int]:
    """
    @return corp_id, alliance_id
    """
    aff = db.session.query(APICacheCharacterAffiliation).filter(APICacheCharacterAffiliation.id == char_id).first()
    if aff is None:
        aff = APICacheCharacterAffiliation()
        aff_info = character_info.get_affiliation_info(char_id)
        aff.id = aff_info['id']
        aff.name = aff_info['name']
        aff.corporationID = aff_info['corporationID']
        aff.corporationName = aff_info['corporationName']
        aff.allianceID = aff_info['allianceID']
        aff.allianceName = aff_info['allianceName']
        aff.expire = aff_info['expire']
        db.session.add(aff)
        db.session.commit()
    else:
        now = datetime.now()
        if aff.expire is None or aff.expire < now:
            aff_info = character_info.get_affiliation_info(char_id)
            aff.name = aff_info['name']
            aff.corporationID = aff_info['corporationID']
            aff.corporationName = aff_info['corporationName']
            aff.allianceID = aff_info['allianceID']
            aff.allianceName = aff_info['allianceName']
            aff.expire = aff_info['expire']
            db.session.commit()
    return aff.corporationID, aff.allianceID
