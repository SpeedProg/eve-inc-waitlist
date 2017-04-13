import logging
from datetime import datetime

from waitlist.storage.database import APICacheCorporationInfo
from waitlist.utility.swagger.eve.corporation import CorporationEndpoint, CorporationInfo
from waitlist import db

logger = logging.getLogger(__name__)


def set_from_corp_info(self: APICacheCorporationInfo, info: CorporationInfo):
    self.name = info.get_corporation_name()
    self.allianceID = info.get_alliance_id()
    self.ceoID = info.get_ceo_id()
    self.description = info.get_corporation_description()
    self.creatorID = info.get_creator_id()
    self.memberCount = info.get_member_count()
    self.taxRate = info.get_tax_rate()
    self.ticker = info.get_ticker()
    self.url = info.get_url()
    self.creationDate = info.get_creation_date()
    self.expire = info.expires()


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

        set_from_corp_info(corp_cache, corp_info)
        db.session.add(corp_cache)
        db.session.commit()
    elif corp_cache.characterName is None:
        corp_ep = CorporationEndpoint()
        corp_info = corp_ep.get_corporation_info(corp_id)
        set_from_corp_info(corp_cache, corp_info)
        db.session.commit()
    else:
        now = datetime.now()
        if corp_cache.expire is None or corp_cache.expire < now:
            # expired, update it
            corp_ep = CorporationEndpoint()
            corp_info = corp_ep.get_corporation_info(corp_id)
            set_from_corp_info(corp_cache, corp_info)
            db.session.commit()

    return corp_cache
