from waitlist.storage.database import APICacheCharacterID, APICacheCharacterInfo, APICacheCharacterAffiliation
from waitlist.base import db
from datetime import datetime
import logging
from waitlist.utility.swagger import character_info

logger = logging.getLogger(__name__)

def get_character_id_from_name(name):
    character = db.session.query(APICacheCharacterID).filter(APICacheCharacterID.name == name).first();
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
        
def get_char_info_for_character(char_id):
    # check cache first
    char_info = db.session.query(APICacheCharacterInfo).filter(APICacheCharacterInfo.id == char_id).first();
    
    if char_info is None:
        char_info = APICacheCharacterInfo()
        result, expires = character_info.get_character_info(char_id)
        corpId = result['corporation_id']
        corpName = result['corporation_name']
        charName = result['name']
        char_info.id = char_id
        char_info.corporationID = corpId
        char_info.corporationName = corpName
        char_info.characterName = charName
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
            corpId = result['corporation_id']
            corpName = result['corporation_name']
            charName = result['name']
            char_info.corporationID = corpId
            char_info.corporationName = corpName
            char_id.characterName = charName
            char_info.expire = expire
            db.session.commit()
    
    return char_info

"""
@return corp_id, alliance_id
"""
def get_affiliation(char_id):
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
        aff.expire = datetime.fromtimestamp(aff_info['expire'])
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
            aff.expire = datetime.fromtimestamp(aff_info['expire'])
            db.session.commit()
    return aff.corporationID, aff.allianceID
