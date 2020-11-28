from flask import Response, jsonify

from waitlist.base import app
from . import models

from . import accounts, characters, i18n
from waitlist.blueprints.swagger_api import statistics


@accounts.bp_v1.errorhandler(403)
@characters.bp_v1.errorhandler(403)
def error_handler_forbidden(ex: Exception) -> Response:
    """
    403 Forbidden error handler for swagger routes
    :param ex: the exception thrown
    :return: an 403 error object
    """
    resp: Response = jsonify(models.errors.error_403(
        "You don't have the required permissions to access this resource."))
    resp.status_code = 403
    return resp

def register_blueprints():
    app.register_blueprint(characters.bp_v1, url_prefix='/swa/v1/characters')
    app.register_blueprint(accounts.bp_v1, url_prefix='/swa/v1/accounts')
    app.register_blueprint(statistics.bp_v1, url_prefix='/swa/v1/statistics')
    app.register_blueprint(i18n.bp_v1, url_prefix='/swa/v1/i18n')
