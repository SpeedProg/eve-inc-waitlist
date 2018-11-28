from datetime import datetime

from flask import request
from flask_login import current_user
from typing import Callable, Dict, Any

from waitlist import app
from waitlist.data.version import version
from waitlist.permissions import perm_manager
from waitlist.utility.config import cdn_eveimg, cdn_eveimg_webp, cdn_eveimg_js, influence_link, title
from waitlist.utility.settings import sget_insert
from waitlist.utility.i18n.locale import get_locale, get_langcode_from_locale
from waitlist.utility.mainmenu import main_nav


def eve_image(browser_webp: bool) -> Callable[[str, str], str]:
    if browser_webp and cdn_eveimg_webp:
        def _eve_image(path: str, _: str) -> str:
            return cdn_eveimg.format(path, 'webp')
    else:
        def _eve_image(path: str, suffix: str) -> str:
            return cdn_eveimg.format(path, suffix)
    return _eve_image


# set if it is the igb
@app.context_processor
def inject_data() -> Dict[str, Any]:
    is_account = False
    if hasattr(current_user, 'type'):
        is_account = (current_user.type == "account")

    header_insert = sget_insert('header')

    req_supports_webp = 'image/webp' in request.headers.get('accept', '')
    eve_image_macro: Callable[[str, str], str] = eve_image(req_supports_webp)
    return dict(version=version,
                perm_manager=perm_manager, header_insert=header_insert,
                eve_proxy_js=cdn_eveimg_js, eve_cdn_webp=cdn_eveimg_webp,
                browserSupportsWebp=req_supports_webp, eve_image=eve_image_macro,
                influence_link=influence_link, is_account=is_account,
                title=title, lang_code=get_langcode_from_locale(get_locale(app)),
                main_nav=main_nav
                )
