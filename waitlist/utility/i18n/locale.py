from flask.globals import request
from flask_login.utils import current_user
from waitlist.utility.account.helpers import get_locale_code
from babel.core import Locale, UnknownLocaleError
from typing import Any
import logging

logger = logging.getLogger(__name__)


def get_locale(app):
    lang_code = get_locale_code(current_user)
    return fix_locale_and_get(lang_code, app)


def fix_locale_and_get(lang_code: str, app: Any) -> Locale:
    from waitlist import db
    logger.debug('lang_code: %s', lang_code)
    if lang_code is None or lang_code not in app.config['LANGUAGES']:
        lang_code = request.accept_languages.best_match(app.config['LANGUAGES'])
        locale = Locale.parse(lang_code)
        current_user.language = lang_code
        db.session.commit()
        return locale
    else:
        try:
            locale = Locale.parse(lang_code)

        except (ValueError, UnknownLocaleError):
            lang_code = request.accept_languages.best_match(
                app.config['LANGUAGES'])
            locale = Locale.parse(lang_code)
            current_user.language = lang_code
            db.session.commit()
        return locale


def get_langcode_from_locale(locale: Locale) -> str:
    lang_code = locale.language
    if locale.territory is not None:
        lang_code = lang_code + '_' + locale.territory
    return lang_code
