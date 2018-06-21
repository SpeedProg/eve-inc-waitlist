from . import bp_v1
from flask.wrappers import Response
from flask_login.utils import login_required, current_user
from waitlist import db
from flask.globals import request
from babel.core import Locale, UnknownLocaleError
from flask import jsonify
from ..models import errors
from waitlist.utility.account.helpers import set_locale_code
from flask.helpers import make_response


@login_required
@bp_v1.route('/locale/',
             methods=['PUT'])
def locale_put_v1() -> Response:
    """
    file: locale_put_v1.yml
    """
    locale_string = request.data.decode('utf-8')
    print(locale_string)
    try:
        Locale.parse(locale_string)
    except (ValueError, UnknownLocaleError):
        resp = jsonify(
            errors.error_404(
                f'Locale {locale_string} not a valid locale code!')
        )
        resp.status_code = 400
        return resp

    set_locale_code(current_user, locale_string)
    db.session.commit()
    return make_response('', 204)
