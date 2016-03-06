from waitlist.storage.database import APICacheCharacterID
from evelink import eve
from waitlist import db

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
        
