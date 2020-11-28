__all__ = ['is_account', 'is_character', 'is_account_or_character']

import flask
from flask import current_app
from flask_principal import identity_changed, AnonymousIdentity
from flask_login import logout_user
from .types import is_account, is_character, is_account_or_character

def force_logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        flask.globals.session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
