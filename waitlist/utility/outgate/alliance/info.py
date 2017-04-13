import logging
from datetime import datetime

from storage.database import APICacheAllianceInfo
from utility.swagger.eve.alliance import AllianceEndpoint
from waitlist import db

logger = logging.getLogger(__name__)


def get_alliance_info(alliance_id: int) -> APICacheAllianceInfo:
    all_cache: APICacheAllianceInfo = db.session.query(APICacheAllianceInfo) \
        .filter(APICacheAllianceInfo.id == alliance_id).first()

    if all_cache is None:
        all_cache = APICacheAllianceInfo()
        all_ep = AllianceEndpoint()
        all_info = all_ep.get_alliance_info(alliance_id)
        if all_info is None:
            # this should never happen
            logger.error(f'No Alliance with id {alliance_id} exists!')

        all_cache.set_from_alliance_info(all_info)
        db.session.add(all_cache)
        db.session.commit()
    elif all_cache.characterName is None:
        all_ep = AllianceEndpoint()
        all_info = all_ep.get_alliance_info(alliance_id)
        all_cache.set_from_alliance_info(all_info)
        db.session.commit()
    else:
        now = datetime.now()
        if all_cache.expire is None or all_cache.expire < now:
            # expired, update it
            all_ep = AllianceEndpoint()
            all_info = all_ep.get_alliance_info(alliance_id)
            all_cache.set_from_alliance_info(all_info)
            db.session.commit()

    return all_cache
