from waitlist.storage.database import APICacheCharacterID, session
from evelink import eve

def get_character_id_from_name(name):
    character = session.query(APICacheCharacterID).filter(APICacheCharacterID.name == name).first();
    if character is None:
        eve_api = eve.EVE()    
        response = eve_api.character_id_from_name(name)
        char_id = int(response.result)
        character = APICacheCharacterID()
        character.id = char_id
        character.name = name
        session.add(character)
        session.commit()
    
    return character.id
        
