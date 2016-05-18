# inject the lib folder before everything else
import os
import sys
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, 'lib'))
from waitlist.storage.database import Account, Character, Role
from waitlist.utility.utils import get_random_token
from waitlist.data.perm import WTMRoles
import evelink
from waitlist.base import db
if __name__ == '__main__':
    name = raw_input("Login Name:")
    pw = raw_input("Password:")
    email = ""
    print "Creating Account"
    acc = Account()
    acc.username = name
    acc.set_password(pw)
    acc.login_token = get_random_token(16)
    acc.email = email
    print "Account created"
    admin_role = db.session.query(Role).filter(Role.name == WTMRoles.admin).first()
    acc.roles.append(admin_role)
    db.session.add(acc)
    print acc.login_token
    
    char_name = "--"
    list_eveids = []
    eve = evelink.eve.EVE()
    while char_name:
        char_name = raw_input("Enter Character to associate with this account:")
        char_name = char_name.strip()
        if not char_name:
            break
        
        response = eve.character_id_from_name(char_name)
        char_id = int(response.result)
        character = Character()
        character.eve_name = char_name
        character.id = char_id
        print("Added "+character.__repr__())
        list_eveids.append(char_id)
        acc.characters.append(character)
    
    db.session.commit()
    
    is_valid = False
    while not is_valid:
        char_id = int(raw_input("Enter charid to set as active char out of "+", ".join([str(i) for i in list_eveids])+":"))
    
        for posid in list_eveids:
            if posid == char_id:
                is_valid = True
                break
    acc.current_char = char_id
    
    db.session.commit()
    print("Admin Account created!")
            