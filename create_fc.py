from waitlist.storage.database import Account, Character, session, Role
from waitlist.utils import get_random_token
from waitlist.permissions import WTMRoles
import evelink
if __name__ == '__main__':
    name = raw_input("Login Name:")
    pw = raw_input("Password:")
    email = ""
    print "Creating Account"
    acc = Account()
    acc.username = name
    acc.set_password(pw)
    acc.login_token = get_random_token(64)
    acc.email = email
    print "Account created"
    fc_role = session.query(Role).filter(Role.name == WTMRoles.fc.name).first()
    acc.roles.append(fc_role)
    session.add(acc)
    print acc.login_token
    
    char_name = "--"
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
        acc.characters.append(character)
    
    session.commit()
    
            