from waitlist.storage.database import APICacheCharacterID, APICacheCharacterInfo,\
    APICacheCorporationInfo
from evelink import eve, api
from waitlist import db
from datetime import datetime

def get_character_id_from_name(name):
    character = db.session.query(APICacheCharacterID).filter(APICacheCharacterID.name == name).first();
    if character is None:
        eve_api = eve.EVE()    
        response = eve_api.character_id_from_name(name)
        char_id = int(response.result)
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
        result = eve.EVE().character_info_from_id(char_id)
        corpId = result.result['corp']['id']
        corpName = result.result['corp']['name']
        expire = datetime.fromtimestamp(result.expires)
        char_info.id = char_id
        char_info.corporationID = corpId
        char_info.corporationName = corpName
        char_info.expire = expire
        db.session.add(char_info)
        db.session.commit()
    else:
        now = datetime.now()
        if char_info.expire < now:
            # expired, update it
            result = eve.EVE().character_info_from_id(char_id)
            corpId = result.result['corp']['id']
            corpName = result.result['corp']['name']
            expire = datetime.fromtimestamp(result.expires)
            char_info.corporationID = corpId
            char_info.corporationName = corpName
            char_info.expire = expire
            db.session.commit()
    
    return char_info

def get_corp_info_for_corporation(corp_id):
    corp_info = db.session.query(APICacheCorporationInfo).filter(APICacheCorporationInfo.id == corp_id).first();
    
    if corp_info is None:
        corp_info = APICacheCorporationInfo()
        result = get_alliance_info(corp_id)
        corp_info.id = corp_id
        corp_info.corporationName = result['corporationName']
        corp_info.allianceID = result['allianceID']
        corp_info.allianceName = result['allianceName']
        corp_info.expire = datetime.fromtimestamp(result['expire'])
        db.session.add(corp_info)
        db.session.commit()
    
    else:
        now = datetime.now()
        if corp_info.expire < now:
            result = get_alliance_info(corp_id)
            corp_info.id = corp_id
            corp_info.corporationName = result['corporationName']
            corp_info.allianceID = result['allianceID']
            corp_info.allianceName = result['allianceName']
            corp_info.expire = datetime.fromtimestamp(result['expire'])
            db.session.commit()
    
    return corp_info

def get_alliance_info(corp_id):
    response = api.API().get('/corp/CorporationSheet', {'corporationID': corp_id})
    
    corpName = response.result.find('corporationName').text
    allianceNameNode = response.result.find('allianceName')
    allianceName = ""
    if allianceNameNode is not None:
        allianceName = allianceNameNode.text
    
    return {'allianceID': response.result.find('allianceID').text, 'allianceName': allianceName, 'corporationName': corpName, 'expire': response.expires}
    