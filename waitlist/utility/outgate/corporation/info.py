import logging
from datetime import datetime

from waitlist import db
from waitlist.storage.database import APICacheCorporationInfo
from waitlist.utility.outgate.exceptions import ESIException, check_esi_response
from waitlist.utility.swagger.eve.corporation import CorporationEndpoint, CorporationInfo

logger = logging.getLogger(__name__)


def set_from_corp_info(self: APICacheCorporationInfo, info: CorporationInfo, corp_id: int):
    self.id = corp_id
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


def get_corp_info(corp_id: int, *args) -> APICacheCorporationInfo:
    corp_cache: APICacheCorporationInfo = db.session.query(APICacheCorporationInfo) \
        .filter(APICacheCorporationInfo.id == corp_id).first()

    if corp_cache is None:
        corp_cache = APICacheCorporationInfo()
        corp_ep = CorporationEndpoint()
        corp_info: CorporationInfo = check_esi_response(corp_ep.get_corporation_info(corp_id), get_corp_info, args)

        set_from_corp_info(corp_cache, corp_info, corp_id)
        db.session.add(corp_cache)
        db.session.commit()
    elif corp_cache.name is None:
        corp_ep = CorporationEndpoint()
        corp_info: CorporationInfo = check_esi_response(corp_ep.get_corporation_info(corp_id), get_corp_info, args)
        set_from_corp_info(corp_cache, corp_info, corp_id)
        db.session.commit()
    else:
        now = datetime.now()
        if corp_cache.expire is None or corp_cache.expire < now:
            # expired, update it
            corp_ep = CorporationEndpoint()
            try:
                corp_info: CorporationInfo = check_esi_response(corp_ep.get_corporation_info(corp_id),
                                                                get_corp_info, args)
            except ESIException:
                return corp_cache
            set_from_corp_info(corp_cache, corp_info, corp_id)
            db.session.commit()

    return corp_cache
