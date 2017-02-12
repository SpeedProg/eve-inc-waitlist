import flask
from flask import current_app
from flask_principal import identity_changed, AnonymousIdentity
from flask_login import current_user, logout_user

from waitlist.data.names import WTMRoles


def get_user_type():
    #0=linemember,1=fc/t,2=lm/r,3=both
    val = -1
    if current_user.is_authenticated:
        val = 0
        if current_user.type == "account":
            is_lm = False
            is_fc = False
            for role in current_user.roles:
                if (role.name == WTMRoles.fc or role.name == WTMRoles.tbadge):
                    is_fc = True
                    if (is_lm):
                        break
                elif (role.name == WTMRoles.lm or role.name == WTMRoles.resident):
                    is_lm = True
                    if (is_fc):
                        break
            if is_fc:
                val += 1
            if is_lm:
                val += 2
    return val

def force_logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        flask.globals.session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())