# inject the lib folder before everything else
from typing import Optional

from waitlist.base import db
from waitlist.permissions.manager import StaticRoles
from waitlist.storage.database import Account, Character, Role, APICacheCharacterInfo
from waitlist.utility.utils import get_random_token
import waitlist.utility.outgate as outgate
if __name__ == '__main__':
    name = input("Login Name:")
    print("Creating Account")
    acc = Account()
    acc.username = name
    acc.login_token = get_random_token(16)
    print("Account created")
    admin_role = db.session.query(Role).filter(Role.name == StaticRoles.ADMIN).first()
    acc.roles.append(admin_role)
    db.session.add(acc)
    print(acc.login_token)
    
    char_name = "--"
    list_eveids = []
    while char_name:
        char_name = input("Enter Character to associate with this account:")
        char_name = char_name.strip()
        if not char_name:
            break
        
        char_info: Optional[APICacheCharacterInfo] = outgate.character.get_info_by_name(char_name)
        char_id = char_info.id
        # assign this too because his name could have had wrong case
        char_name = char_info.characterName
        character: Character = db.session.query(Character).get(char_id)
        if character is None:
            character = Character()
            character.eve_name = char_name
            character.id = char_id
        print("Added "+character.__repr__())
        list_eveids.append(char_id)
        acc.characters.append(character)
    
    db.session.commit()
    
    is_valid = False
    char_id = None
    while not is_valid:
        char_id = int(input("Enter charid to set as active char out of "+", ".join([str(i) for i in list_eveids])+":"))
    
        for posid in list_eveids:
            if posid == char_id:
                is_valid = True
                break
    acc.current_char = char_id
    
    db.session.commit()
    print("Admin Account created!")

