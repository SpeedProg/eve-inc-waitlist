import logging
from datetime import datetime

from storage.database import APICacheCorporationInfo
from utility.swagger.eve.corporation import CorporationEndpoint
from waitlist import db

logger = logging.getLogger(__name__)


def get_corp_info(corp_id: int) -> APICacheCorporationInfo:
    corp_cache: APICacheCorporationInfo = db.session.query(APICacheCorporationInfo) \
        .filter(APICacheCorporationInfo.id == corp_id).first()

    if corp_cache is None:
        corp_cache = APICacheCorporationInfo()
        corp_ep = CorporationEndpoint()
        corp_info = corp_ep.get_corporation_info(corp_id)
        if corp_info is None:
            # this should never happen
            logger.error(f'No Corp with id {corp_id} exists!')

        corp_cache.set_from_corp_info(corp_info)
        db.session.add(corp_cache)
        db.session.commit()
    elif corp_cache.characterName is None:
        corp_ep = CorporationEndpoint()
        corp_info = corp_ep.get_corporation_info(corp_id)
        corp_cache.set_from_corp_info(corp_info)
        db.session.commit()
    else:
        now = datetime.now()
        if corp_cache.expire is None or corp_cache.expire < now:
            # expired, update it
            corp_ep = CorporationEndpoint()
            corp_info = corp_ep.get_corporation_info(corp_id)
            corp_cache.set_from_corp_info(corp_info)
            db.session.commit()

    return corp_cache
