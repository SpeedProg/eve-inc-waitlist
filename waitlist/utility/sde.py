import logging
from bz2 import BZ2File
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Union, Optional, List, Tuple

import flask
from esipy import EsiClient
from pyswagger import App
from yaml.events import MappingStartEvent, ScalarEvent, MappingEndEvent
import yaml
from waitlist.storage.database import InvType, Station, Constellation,\
    SolarSystem, IncursionLayout
from waitlist import db
from os import path, PathLike
import csv

from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve import get_esi_client

logger = logging.getLogger(__name__)


def update_invtypes(filepath: str):
    # this might be better off writing a specific parser for performance, yaml is really slow
    inv_type = None
    att_name = None
    subatt_name = None
    mapping_count = 0
    filename = filepath

    if not path.isfile(filename):
        return

    if filename.rsplit('.', 1)[1] == "yaml":
        f = open(filename, 'rb')
    elif filename.rsplit('.', 1)[1] == "bz2":
        f = BZ2File(filename)
    else:
        return

    for ev in yaml.parse(f):
        if isinstance(ev, MappingStartEvent):
            mapping_count += 1
        elif isinstance(ev, ScalarEvent):
            if mapping_count == 1:
                inv_type = InvType()
                inv_type.typeID = int(ev.value)
            if mapping_count == 2:
                if att_name is None:
                    att_name = ev.value
                else:
                    if att_name == "groupID":
                        inv_type.groupID = int(ev.value)
                    elif att_name == "marketGroupID":
                        inv_type.marketGroupID = int(ev.value)

                    att_name = None
            if mapping_count == 3:
                # when it gets where att_name should be the value of the upper thing
                # should probably just put stuff into a list
                if subatt_name is None:
                    subatt_name = ev.value
                else:  # we have the value
                    if att_name == 'name' and subatt_name == 'en':
                        inv_type.typeName = ev.value
                    elif att_name == 'description' and subatt_name == 'en':
                        inv_type.description = ev.value
                    
                    subatt_name = None
        elif isinstance(ev, MappingEndEvent):
            if mapping_count == 3:
                att_name = None
                subatt_name = None
            elif mapping_count == 2:
                att_name = None
                db.session.merge(inv_type)

            mapping_count -= 1
    
    f.close()
    db.session.commit()
    db.session.close()


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
    for ev in yaml.parse(f):
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
    esi_client: EsiClient = get_esi_client(True)
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
        #esi_client: EsiClient = get_esi_client(True)
        api: App = get_api()
        const_request = api.op['get_universe_constellations_constellation_id'](constellation_id=const_id)
        print(f"Requesting Const {const_id}")
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
        print(e)
        return const_id, esi_client


def update_systems() -> int:
    esi_client: EsiClient = get_esi_client(True)
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
        #esi_client: EsiClient = get_esi_client(True)
        api: App = get_api()
        system_request = api.op['get_universe_systems_system_id'](system_id=system_id)
        print(f"Requesting System {system_id}")
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
        print(e)
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
