from waitlist.storage.database import Account
from waitlist.utils import get_random_token
from waitlist import storage
from waitlist.permissions import WTMRoles
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
    acc.roles.append(WTMRoles.fc)
    storage.database.session.add(acc)
    storage.database.session.commit()
    print acc.login_token