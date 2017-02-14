from datetime import datetime

from flask import request
from flask.ext.login import current_user

from waitlist import app
from waitlist.data import version
from waitlist.permissions import perm_manager
from waitlist.utility.account import get_user_type
from waitlist.utility.config import cdn_eveimg, cdn_eveimg_webp, cdn_eveimg_js
from waitlist.utility.settings.settings import sget_insert
from waitlist.data.perm import perm_management, perm_settings, perm_admin,\
    perm_officer, perm_accounts, perm_feedback, perm_dev, perm_leadership,\
    perm_bans, perm_viewfits, perm_comphistory, perm_mod_mail_resident,\
    perm_mod_mail_tbadge


def eve_image(browser_webp):
    if browser_webp and cdn_eveimg_webp:
        def _eve_image(path, _):
            return cdn_eveimg.format(path, 'webp')
    else:
        def _eve_image(path, suffix):
            return cdn_eveimg.format(path, suffix)
    return _eve_image


# set if it is the igb
@app.context_processor
def inject_data():
    is_account = False
    if hasattr(current_user, 'type'):
        is_account = (current_user.type == "account")
    header_insert = sget_insert('header')

    current_time = datetime.utcnow()
    end_time = datetime(2016, 8, 7, 11, 0, 0)
    start_time = datetime(2016, 7, 4, 11, 0, 0)
    cc_vote_on = (start_time > current_time > end_time)

    if header_insert is not None:
        header_insert = header_insert.replace("$type$", str(get_user_type()))
    if 'image/webp' in request.headers.get('accept'):
        req_supports_webp = True
    else:
        req_supports_webp = False
    eve_image_macro = eve_image(req_supports_webp)
    return dict(perm_admin=perm_admin, perm_settings=perm_settings,
                perm_man=perm_management, perm_officer=perm_officer,
                perm_accounts=perm_accounts, perm_feedback=perm_feedback,
                is_account=is_account, perm_dev=perm_dev, perm_leadership=perm_leadership,
                perm_bans=perm_bans, perm_viewfits=perm_viewfits, version=version,
                perm_comphistory=perm_comphistory, perm_res_mod=perm_mod_mail_resident,
                perm_t_mod=perm_mod_mail_tbadge, perm_manager=perm_manager, header_insert=header_insert,
                eve_proxy_js=cdn_eveimg_js, eve_cdn_webp=cdn_eveimg_webp, browserSupportsWebp=req_supports_webp,
                eve_image=eve_image_macro, ccvote_on=cc_vote_on
                )
