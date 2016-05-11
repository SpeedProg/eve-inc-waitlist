from waitlist.storage.database import APICacheCharacterID, APICacheCharacterInfo,\
    APICacheCorporationInfo, APICacheCharacterAffiliation
from evelink import eve, api
from waitlist.base import db
from datetime import datetime

def get_character_id_from_name(name):
    character = db.session.query(APICacheCharacterID).filter(APICacheCharacterID.name == name).first();
    if character is None:
        eve_api = eve.EVE()    
        response = eve_api.character_id_from_name(name)
        if response.result is None:
            return 0
        char_id = int(response.result)
        if char_id == 0:
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
        if char_info.expire is None or char_info.expire < now:
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

"""
@return corp_id, alliance_id
"""
def get_affiliation(char_id):
    aff = db.session.query(APICacheCharacterAffiliation).filter(APICacheCharacterAffiliation.id == char_id).first()
    if aff is None:
        aff = APICacheCharacterAffiliation()
        aff_info = get_affiliation_info(char_id)
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
            aff_info = get_affiliation_info(char_id)
            aff.name = aff_info['name']
            aff.corporationID = aff_info['corporationID']
            aff.corporationName = aff_info['corporationName']
            aff.allianceID = aff_info['allianceID']
            aff.allianceName = aff_info['allianceName']
            aff.expire = datetime.fromtimestamp(aff_info['expire'])
            db.session.commit()
    
    return aff.corporationID, aff.allianceID

# object = {'id':char_id, 'name': char_name, 'allianceID': alliance_id, 'allianceName': alliance_name, 'corporationID': corp_id, 'corporationName': corp_name, 'expire': expire}
def get_affiliation_info(char_id):
    eve_obj = eve.EVE()
    response = eve_obj.affiliations_for_character(char_id)
    char_id = response.result['id']
    char_name = response.result['name']
    corp_id = response.result['corp']['id']
    corp_name = response.result['corp']['name']
    if "alliance" in response.result:
        alliance_id = response.result['alliance']['id']
        alliance_name = response.result['alliance']['name']
    else:
        alliance_id = 0
        alliance_name = ""
    return {'id':char_id, 'name': char_name, 'allianceID': alliance_id, 'allianceName': alliance_name, 'corporationID': corp_id, 'corporationName': corp_name, 'expire': response.expires}

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
        if corp_info.expire is None or corp_info.expire < now:
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

def eve_api_cache_char_ids(characters):
    # filter out characters that we know
    characters = [char for char in characters if not is_char_cached(char)]
    
    if len(characters) == 0:
        return
    
    f = lambda A, n=100: [A[i:i+n] for i in range(0, len(A), n)]
    char_lists = f(characters)
    eve = api.API()
    for char_list in char_lists:
        response = eve.get('eve/CharacterID', {'names': ",".join(char_list)})
        rows = response.result.find('rowset').findall('row')
        for row in rows:
            c_id = int(row.get('characterID'))
            if c_id == 0:
                continue
            c_name = row.get('name')
            character = db.session.query(APICacheCharacterID).filter(APICacheCharacterID.id == c_id).first();
            if character is None:
                character = APICacheCharacterID()
                character.id = c_id
                character.name = c_name
                db.session.add(character)
        db.session.commit()

def is_char_cached(char_name):
    character = db.session.query(APICacheCharacterID).filter(APICacheCharacterID.name == char_name).first();#
    return (character is not None)
            