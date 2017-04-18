import logging
from datetime import datetime

from waitlist.storage.database import APICacheAllianceInfo
from waitlist.utility.outgate.exceptions import check_esi_response
from waitlist.utility.swagger.eve.alliance import AllianceEndpoint, AllianceInfo
from waitlist import db

logger = logging.getLogger(__name__)


def set_from_alliance_info(self: APICacheAllianceInfo, info: AllianceInfo):
    self.allianceName = info.get_alliance_name()
    self.dateFounded = info.get_date_founded()
    self.executorCorpID = info.get_executor_corp_id()
    self.ticker = info.get_ticker()
    self.expire = info.expires()


def get_alliance_info(alliance_id: int, *args) -> APICacheAllianceInfo:
    all_cache: APICacheAllianceInfo = db.session.query(APICacheAllianceInfo) \
        .filter(APICacheAllianceInfo.id == alliance_id).first()

    if all_cache is None:
        all_cache = APICacheAllianceInfo()
        all_ep = AllianceEndpoint()
        all_info: AllianceInfo = check_esi_response(all_ep.get_alliance_info(alliance_id), get_alliance_info, args)

        set_from_alliance_info(all_cache, all_info)
        db.session.add(all_cache)
        db.session.commit()
    elif all_cache.characterName is None:
        all_ep = AllianceEndpoint()
        all_info: AllianceInfo = check_esi_response(all_ep.get_alliance_info(alliance_id), get_alliance_info, args)
        set_from_alliance_info(all_cache, all_info)
        db.session.commit()
    else:
        now = datetime.now()
        if all_cache.expire is None or all_cache.expire < now:
            # expired, update it
            all_ep = AllianceEndpoint()
            all_info: AllianceInfo = check_esi_response(all_ep.get_alliance_info(alliance_id), get_alliance_info, args)
            set_from_alliance_info(all_cache, all_info)
            db.session.commit()

    return all_cache
