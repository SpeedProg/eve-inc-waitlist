import logging
from bz2 import BZ2File
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, Optional, Tuple, List
from collections import deque
from sqlalchemy.sql import exists
import flask
from esipy import EsiClient
from yaml.events import MappingStartEvent, ScalarEvent, MappingEndEvent
import yaml
from waitlist.storage.database import InvType, Station, Constellation,\
    SolarSystem, IncursionLayout, InvCategory, InvGroup,\
    InvTypeDogmaAttribute, InvTypeDogmaEffect, MarketGroup
from waitlist.base import db
from os import path, PathLike
import csv

from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve import get_esi_client
from waitlist.utility.swagger.eve.universe import UniverseEndpoint
from waitlist.utility.swagger.eve.market import MarketEndpoint, MarketGroupResponse
from waitlist.utility.utils import chunks
import time

logger = logging.getLogger(__name__)

def get_descendents(responses: List[MarketGroupResponse], parent_id: int) -> List[MarketGroupResponse]:
    descendents: List[MarketGroupResponse] = [resp for resp in responses if resp.parent_id == parent_id]
    return descendents

def update_market_groups():
    """This updates all MarketGroups
    No Commit is done
    """
    logger.debug('update_market_groups')
    ep: MarketEndpoint = MarketEndpoint()
    groups_resp: MarketGroupsResponse = ep.get_groups()

    upstream_group_ids = set(groups_resp.data)
    db_marketgroup_ids = { gid for gid, in db.session.query(MarketGroup.marketGroupID) }
    not_in_upstream = db_marketgroup_ids - upstream_group_ids
    not_in_db = upstream_group_ids - db_marketgroup_ids
    in_db_and_upstream = upstream_group_ids.intersection(db_marketgroup_ids)
    logger.debug('upstream: %r db: %r', upstream_group_ids, db_marketgroup_ids)
    logger.debug('not upstream: %r not_db: %r both: %r', not_in_upstream, not_in_db, in_db_and_upstream)
    # lets delete marketgroups what don't exist anymore first
    logger.info("Deleting market groups: %r", not_in_upstream)
    # this can't be done by 'evaluate' so we use 'fetch'
    db.session.query(MarketGroup)\
        .filter(MarketGroup.marketGroupID.in_(not_in_upstream))\
        .delete(synchronize_session='fetch')


    market_group_responses: List[MarketGroupResponse] = []
    ids_that_need_checking = list(not_in_db)
    ids_that_need_checking.extend(in_db_and_upstream)
    for mg_id_chunk in chunks(ids_that_need_checking, 1000):
        market_group_responses.extend(ep.get_group_multi(mg_id_chunk))

    # now go through them hierarchically
    base_groups: List[MarketGroupResponse] = []
    for market_group_resp in market_group_responses:
        if market_group_resp.parent_id is None:
            base_groups.append(market_group_resp)

    # now we can walk them all from the base
    mg_add_list = []
    mg_update_list = []
    stack = []
    for base_market_group in base_groups:
        stack.append(base_market_group)
        while len(stack) > 0:
            current = stack.pop()
            if current.id in not_in_db:
                mg_add_list.append(dict(
                    marketGroupID=current.id,
                    parentGroupID=current.parent_id,
                    marketGroupName=current.name,
                    description=current.description,
                    iconID=0,
                    hasTypes=(len(current.types) > 0)
                ))
            elif current.id in in_db_and_upstream:
                mg_update_list.append(dict(
                    marketGroupID=current.id,
                    parentGroupID=current.parent_id,
                    marketGroupName=current.name,
                    description=current.description,
                    iconID=0,
                    hasTypes=(len(current.types) > 0)
                ))

            for desc in get_descendents(market_group_responses, current.id):
                stack.append(desc)




    logger.debug('Inserting MarketGroups: %r', mg_add_list)
    logger.debug('Updating MarketGroups: %r', mg_update_list)
    db.session.bulk_insert_mappings(MarketGroup, mg_add_list)
    db.session.bulk_update_mappings(MarketGroup, mg_update_list)


def add_marketgroup_by_id_to_database(market_group_id: int):
    """Adds a MarketGroup to database
       This does not commit!
    """
    if market_group_id is None:
        logger.warning('add_marketgroup_by_id_to_database was called with None')
        return

    if db.session.query(exists().where(MarketGroup.marketGroupID == market_group_id)).scalar():
        return

    ep: MarketEndpoint = MarketEndpoint()
    resp: MarketGroupResponse = ep.get_group(market_group_id)
    current: MarketGroupResponse = resp
    # this will hold the groups and their parents
    # starting with the lowest child
    # so they need to be added in reverse order to database
    groups_to_add: List[MarketGroupResponse] = []
    cur.append(resp)
    # we have the path to root if it has no parent or parent is already in database
    while current.parent_id is not None and not db.session.query(exists().where(MarketGroup.marketGroupID == current.parent_id)):
        reps = ep.get_group(current.parent_id)
        parents_to_add.append(current)
        current = resp

    bulk_data = deque(maxlen=len(groups_to_add))
    for group in groups_to_add:
        bulk_data.appendleft(dict(
            marketGroupID=group.id,
            parentGroupID=group.parent_id,
            marketGroupName=group.name,
            description=group.description,
            iconID=0, # this is not in esi
            hasTypes=(len(group.types) > 0)
        ))
    db.session.bulk_insert_mappings(MarketGroup, bulk_data)

def add_invgroup_by_id_to_database(invgroup_id: int):
    """Adds a InvGroup to database
       This does not commit!
    """
    if invgroup_id is None:
        logger.warning('add_invgroup_by_id_to_database was called with None')
        return

    if db.session.query(exists().where(InvGroup.groupID == invgroup_id)).scalar():
        return
    ep: UniverseEndpoint = UniverseEndpoint()
    resp: GroupResponse = ep.get_group(invgroup_id)
    add_invcategory_by_id_to_database(resp.invcategory_id)

    group: InvGroup = InvGroup(
        groupID=resp.id,
        groupName=resp.name,
        published=resp.published,
        categoryID=resp.category_id,
    )
    db.session.add(group)

def add_invcategory_by_id_to_database(invcategory_id: int):
    """Adds a InvCategory to datase
       This does not commit!
    """
    if invcategory_id is None:
        logger.warning('add_invcategory_by_id_to_database was called with None as argument')
        return

    if db.session.query(exists().where(InvCategory.categoryID == invcategory_id)).scalar():
        return

    ep: UniverseEndpoint = UniverseEndpoint()
    resp: CategoryResponse = ep.get_category(invcategory_id)
    cat: InvCategory = InvCategory(
        categoryID=resp.id,
        categoryName=resp.name,
        published=resp.published
    )
    db.session.add(cat)

def add_type_by_id_to_database(type_id: int):
    """Add a new type by id to database
       only call this if you are sure the type does not exist
       This does not call commit!
    """
    ep: UniverseEndpoint = UniverseEndpoint()
    resp = ep.get_type(type_id)

    # add foreign key objects if we don't have them
    add_marketgroup_by_id_to_database(resp.market_group_id)
    add_invgroup_by_id_to_database(resp.group_id)

    type_db: InvType = InvType(
        typeID=resp.type_id,
        groupID=resp.group_id,
        typeName=resp.name,
        description=resp.description,
        marketGroupID=resp.market_group_id)

    db.session.add(type_db)

    if resp.dogma_attributes is not None:
        for attr_info in resp.dogma_attributes:
            dogma_attr = InvTypeDogmaAttribute(
                typeID=resp.type_id,
                attributeID=attr_info['attribute_id'],
                value=attr_info['value'])
            db.session.add(dogma_attr)


    if resp.dogma_effects is not None:
        for effect in resp.dogma_effects:
            effect_data = InvTypeDogmaEffect(
                typeID=resp.type_id,
                effectID=effect['effect_id'],
                isDefault=effect['is_default'])
            db.session.add(effect_data)


def update_categories_and_groups():
    """This updates Inventory Categories and Groups
    No Commit is done
    """
    ep: UniverseEndpoint = UniverseEndpoint()

    categories_start = time.time()

    categories_resp: CategoriesResponse = ep.get_categories()
    upstream_cat_ids = categories_resp.data
    logger.debug('CategoryIDs Upstream: %r', upstream_cat_ids)
    # this is going to hold a list with all group ids these categories have
    # we can use this later and don't need to request all groups
    # this way we might miss groups without category but
    # those are of no interest to us anyway
    group_ids: Set[int] = set()
    category_ids_db: List[int] = [row[0] for row in db.session.query(
        InvCategory.categoryID).all()]
    logger.debug('CategoryIDs in database: %r', category_ids_db)
    # find categories that don't exist anymore
    category_ids_to_remove: List[int] = [db_id for db_id in category_ids_db
                                         if db_id not in upstream_cat_ids]
    # remove categories from db if they don't exist anymore
    # this removes their groups by cascading
    logger.info('Categories to remove: %r', category_ids_to_remove)
    for cat_id in category_ids_to_remove:
        db.session.query(InvCategory).filter(
            InvCategory.categoryID == cat_id).delete(
                synchronize_session='evaluate')

    update_categories: List[Dict[str, Any]] = []
    insert_categories: List[Dict[str, Any]] = []
    for cat_chunk in chunks(upstream_cat_ids, 1000):
        logger.debug('Updating: %r', cat_chunk)
        cat_info_responses: List[CategoryResponse] = ep.get_category_multi(
            cat_chunk)
        for cat_data_resp in cat_info_responses:
            for group_id in cat_data_resp.groups:
                group_ids.add(group_id)

            data = dict(
                categoryID=cat_data_resp.id,
                categoryName=cat_data_resp.name,
                published=cat_data_resp.published)

            if cat_data_resp.id in category_ids_db:
                update_categories.append(data)
            else:
                insert_categories.append(data)

    logger.debug('Insert: %r', insert_categories)
    logger.debug('Update: %r', update_categories)
    db.session.bulk_update_mappings(InvCategory, update_categories)
    db.session.bulk_insert_mappings(InvCategory, insert_categories)

    categories_end = time.time()
    logger.info('Categories updated in %s',
                categories_end - categories_start)

    group_ids = list(group_ids)
    group_ids.sort()

    logger.debug('GroupIDs Upstream: %r', group_ids)
    # now all categories should be up to date
    # lets update our groups

    groups_start = time.time()

    group_ids_db: List[int] = [row[0] for row in db.session.query(
        InvGroup.groupID).all()]
    logger.debug('GroupIDs in database: %r', group_ids_db)
    # find groups that don't exist anymore
    group_ids_to_remove: List[int] = [db_id for db_id in group_ids_db
                                      if db_id not in group_ids]
    logger.info('GroupIDs to remove: %r', group_ids_to_remove)
    # remove groups from db if they don't exist anymore
    # this removes their groups by cascading
    for group_id in group_ids_to_remove:
        db.session.query(InvGroup).filter(
            InvGroup.groupID == group_id).delete(
                synchronize_session='evaluate')

    update_groups: List[Dict[str, Any]] = []
    insert_groups: List[Dict[str, Any]] = []
    for group_chunk in chunks(group_ids, 1000):
        logger.debug('Updating: %r', group_chunk)
        group_info_responses: List[GroupResponse] = ep.get_group_multi(
            group_chunk)
        for group_data_resp in group_info_responses:
            data = dict(
                groupID=group_data_resp.id,
                groupName=group_data_resp.name,
                published=group_data_resp.published,
                categoryID=group_data_resp.category_id
                )
            if int(group_data_resp.id) in group_ids_db:
                update_groups.append(data)
            else:
                insert_groups.append(data)

    logger.debug('Insert: %r', insert_groups)
    logger.debug('Update: %r', update_groups)
    db.session.bulk_update_mappings(InvGroup, update_groups)
    db.session.bulk_insert_mappings(InvGroup, insert_groups)

    groups_end = time.time()
    logger.info('Groups updated in %s',
                groups_end - groups_start)


def update_invtypes():
    """ Updates Inventory Types and their Categories and Groups
    :throws ApiException is thrown if an error exists
    """
    all_start = time.time()
    ep: UniverseEndpoint = UniverseEndpoint()
    update_market_groups()
    update_categories_and_groups()

    types_start = time.time()

    type_responses: List[TypesResponse] = ep.get_types()

    existing_inv_ids: List[int] = []
    for resp in type_responses:
        for type_id in resp.data:
            existing_inv_ids.append(type_id)
    existing_inv_ids.sort()

    logger.debug('InvTypeIDs Upstream: %r', existing_inv_ids)

    invtype_ids_db: List[int] = [row[0] for row in db.session.query(
        InvType.typeID).order_by(InvType.typeID).all()]
    logger.debug('InvTypeIDs in database: %r', invtype_ids_db)

    invtype_ids_to_remove: List[int] = [db_id for db_id in invtype_ids_db
                                        if db_id not in existing_inv_ids]
    # remove categories from db if they don't exist anymore
    # this removes their groups by cascading
    logger.info('InvtypeIDs to remove: %r', invtype_ids_to_remove)
    for invtype_id in invtype_ids_to_remove:
        # this is a speciall case cause by auto increment
        # if the name of the ivntype is #System
        # we should update it to id=0
        if invtype_id == 1:
            invtype: InvType = db.session.query(InvType).get(1)
            if invtype.typeName == '#System':
                invtype.typeID = 0
                invtype_ids_db.remove(1)
                if 0 not in invtype_ids_db:
                    invtype_ids_db.append(0)
                    invtype_ids_db.sort()
                continue

        db.session.query(InvType).filter(
            InvType.typeID == invtype_id).delete(
                synchronize_session='evaluate')

    # lets update these in 1k chunks a time
    for typeid_chunk in chunks(existing_inv_ids, 5000):
        logger.debug('Updating InvTypes: %r', typeid_chunk)
        # lets load it first
        update_type: List[Dict[str, Any]] = []
        insert_type: List[Dict[str, Any]] = []
        insert_attribute: List[Dict[str, Any]] = []
        insert_effect: List[Dict[str, Any]] = []
        t_start = time.time()
        responses = ep.get_type_multi(typeid_chunk)
        t_end = time.time()
        logger.info('Loading chunk of size %d took %s', len(typeid_chunk),
                    t_end-t_start)
        # now go over the types in the responses
        for resp in responses:
            logger.debug('Working on InvType: %d', resp.type_id)
            data = dict(
                typeID=resp.type_id,
                groupID=resp.group_id,
                typeName=resp.name,
                description=resp.description,
                marketGroupID=resp.market_group_id)

            if resp.type_id in invtype_ids_db:
                logger.debug('Needs Update')
                update_type.append(data)
                # lets just remove all attrs and effects
                # and add them again later
                db.session.query(
                    InvTypeDogmaAttribute).filter(
                        InvTypeDogmaAttribute.typeID == resp.type_id).delete(
                            synchronize_session='evaluate')
                db.session.query(
                    InvTypeDogmaEffect).filter(
                        InvTypeDogmaEffect.typeID == resp.type_id).delete(
                            synchronize_session='evaluate')
            else:
                logger.debug('Needs Insert')
                insert_type.append(data)

            if resp.dogma_attributes is not None:
                for attr_info in resp.dogma_attributes:
                    attr_data = dict(
                        typeID=resp.type_id,
                        attributeID=attr_info['attribute_id'],
                        value=attr_info['value'])
                    insert_attribute.append(attr_data)

            if resp.dogma_effects is not None:
                for effect in resp.dogma_effects:
                    effect_data = dict(
                        typeID=resp.type_id,
                        effectID=effect['effect_id'],
                        isDefault=effect['is_default'])
                    insert_effect.append(effect_data)

        logger.debug('Insert: %r', insert_type)
        logger.debug('Update: %r', update_type)
        db.session.bulk_update_mappings(InvType, update_type)
        db.session.bulk_insert_mappings(InvType, insert_type)
        db.session.bulk_insert_mappings(InvTypeDogmaAttribute,
                                        insert_attribute)
        db.session.bulk_insert_mappings(InvTypeDogmaEffect,
                                        insert_effect)
        db.session.commit()

    all_end = time.time()
    logger.info('InvTypes updated in %s', all_end - types_start)
    logger.info('Categories, Groups and InvTypes updated in %s',
                all_end - all_start)


def update_stations(filename):
    if not path.isfile(filename):
        return

    if filename.rsplit('.', 1)[1] == "yaml":
        f = open(filename, 'r')
    elif filename.rsplit('.', 1)[1] == "bz2":
        f = BZ2File(filename)
    else:
        return

    next_scalar_type = "key"
    station = None
    att_key = None
    for ev in yaml.parse(f, Loader=yaml.SafeLoader):
        if isinstance(ev, MappingStartEvent):
            # 1 mapping per station
            station = Station()  # create new station
            next_scalar_type = "key"
        elif isinstance(ev, ScalarEvent):
            if next_scalar_type == "key":
                att_key = ev.value
                next_scalar_type = "value"
            elif next_scalar_type == "value":
                att_value = ev.value
                if att_key == "stationName":
                    station.stationName = att_value
                elif att_key == "stationID":
                    station.stationID = int(att_value)
                next_scalar_type = "key"
        elif isinstance(ev, MappingEndEvent):
            # write it
            db.session.merge(station)

    db.session.commit()

    f.close()


def update_constellations() -> int:
    esi_client: EsiClient = get_esi_client(None, True)
    api: App = get_api()
    consts_request = api.op['get_universe_constellations']()

    consts_resp = esi_client.request(consts_request)
    if consts_resp.status != 200:
        flask.abort(500, 'Could not get constellation ids from ESI')
    futures: List[Future] = []
    with ThreadPoolExecutor(max_workers=500) as executor:
        for const_id in consts_resp.data:
            futures.append(executor.submit(add_constellation_info, const_id, esi_client))
        # re request if it throws an exception
        while len(futures) > 0:
            nfutures: List[Future] = []
            for f in as_completed(futures):
                r: Optional[Tuple[int, EsiClient]] = f.result()
                if r is not None:
                    nfutures.append(executor.submit(add_constellation_info, r[0], r[1]))
            futures = nfutures
    # with waits for all tasks to finish as if .shutdown(True) was called
    return len(consts_resp.data)


def add_constellation_info(const_id: int, esi_client: EsiClient) -> Optional[Tuple[int, EsiClient]]:
    try:
        api: App = get_api()
        const_request = api.op['get_universe_constellations_constellation_id'](constellation_id=const_id)

        const_resp = esi_client.request(const_request)
        if const_resp.status != 200:
            logger.error(f'Could not get constellation info for id={const_id} status={const_resp.status}')
            return
        const = Constellation()
        const.constellationID = const_resp.data['constellation_id']
        const.constellationName = const_resp.data['name']
        db.session.merge(const)
        db.session.commit()
        return None
    except Exception as e:
        return const_id, esi_client


def update_systems() -> int:
    esi_client: EsiClient = get_esi_client(None, True)
    api: App = get_api()
    systems_request = api.op['get_universe_systems']()
    systems_resp = esi_client.request(systems_request)
    if systems_resp.status != 200:
        flask.abort(500, 'Could not get system ids from ESI')
    futures: List[Future] = []
    with ThreadPoolExecutor(max_workers=500) as executor:
        for system_id in systems_resp.data:
            futures.append(executor.submit(add_system_info, system_id, esi_client))
        # re request if it throws an exception
        while len(futures) > 0:
            nfutures: List[Future] = []
            for f in as_completed(futures):
                r: Optional[Tuple[int, EsiClient]] = f.result()
                if r is not None:
                    nfutures.append(executor.submit(add_system_info, r[0], r[1]))
            futures = nfutures

    return len(systems_resp.data)
    # with waits for all tasks to finish as if .shutdown(True) was called


def add_system_info(system_id: int, esi_client: EsiClient) -> Optional[Tuple[int, EsiClient]]:
    try:
        api: App = get_api()
        system_request = api.op['get_universe_systems_system_id'](system_id=system_id)
        system_resp = esi_client.request(system_request)
        if system_resp.status != 200:
            logger.error(f'Could not get systen info for id={system_id} status={system_resp.status}')
            return
        system = SolarSystem()
        system.solarSystemID = system_resp.data['system_id']
        system.solarSystemName = system_resp.data['name']
        db.session.merge(system)
        db.session.commit()
        return None
    except Exception as e:
        return system_id, esi_client


def update_layouts(filename: Union[str, PathLike]):
    key_const = "Constellation"
    # key_staging = "Staging System"
    key_hq = "Headquarter System"
    key_dock = "Dockup"
    if not path.isfile(filename):
        return

    if filename.rsplit('.', 1)[1] == "csv":
        f = open(filename, 'r')
    elif filename.rsplit('.', 1)[1] == "bz2":
        f = BZ2File(filename)
    else:
        return

    reader = csv.DictReader(f, delimiter="\t", quotechar='\\')
    for row in reader:
        constellation = db.session.query(Constellation)\
            .filter(Constellation.constellationName == row[key_const]).first()
        if constellation is None:
            continue
        # staging = db.session.query(SolarSystem).filter(SolarSystem.solarSystemName == row[key_staging]).first()
        hq = db.session.query(SolarSystem).filter(SolarSystem.solarSystemName == row[key_hq]).first()
        dock = db.session.query(Station).filter(Station.stationName == row[key_dock]).first()
        if hq is None or dock is None:
            continue
        
        inc_const = IncursionLayout()
        inc_const.constellation = constellation.constellationID
        # inc_const.staging = staging.solarSystemID
        inc_const.headquarter = hq.solarSystemID
        inc_const.dockup = dock.station_id
        db.session.merge(inc_const)

    f.close()
    db.session.commit()
