from datetime import datetime

from flask import request
from flask_login import current_user
from typing import Callable, Dict, Any

from waitlist import app
from waitlist.data.version import version
from waitlist.permissions import perm_manager
from waitlist.utility import config
from waitlist.utility.config import cdn_eveimg, cdn_eveimg_webp, cdn_eveimg_js
from waitlist.utility.settings import sget_insert


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

    current_time: datetime = datetime.utcnow()
    end_time: datetime = datetime(2016, 8, 7, 11, 0, 0)
    start_time: datetime = datetime(2016, 7, 4, 11, 0, 0)
    cc_vote_on: bool = ((start_time < current_time) and (current_time < end_time))

    if request.headers.get('accept') is not None and (
     'image/webp' in request.headers.get('accept')):
        req_supports_webp = True
    else:
        req_supports_webp = False
    eve_image_macro: Callable[[str, str], str] = eve_image(req_supports_webp)
    return dict(version=version,
                perm_manager=perm_manager, header_insert=header_insert,
                eve_proxy_js=cdn_eveimg_js, eve_cdn_webp=cdn_eveimg_webp, browserSupportsWebp=req_supports_webp,
                eve_image=eve_image_macro, ccvote_on=cc_vote_on,
                influence_link=config.influence_link, is_account=is_account,
                title=config.title, config=config
                )
