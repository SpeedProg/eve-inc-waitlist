from bz2 import BZ2File
from yaml.events import MappingStartEvent, ScalarEvent, MappingEndEvent
import yaml
from waitlist.storage.database import InvType, Station, Constellation,\
    SolarSystem, IncursionLayout
from waitlist.base import db
from os import path
import csv
import sqlite3
def update_invtypes(filepath):
    # this might be better off writing a specific parser for performance, yaml is really slow
    inv_type = None
    att_name = None
    subatt_name = None
    mapping_count = 0
    filename = filepath

    if not path.isfile(filename):
        return

    if filename.rsplit('.', 1)[1] == "yaml" :
        f = open(filename, 'r')
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
                if att_name == None:
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
                if subatt_name == None:
                    subatt_name = ev.value
                else:# we have the value
                    if att_name == u'name' and subatt_name == u'en':
                        inv_type.typeName = ev.value
                    elif att_name == u'description' and subatt_name == u'en':
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

    if filename.rsplit('.', 1)[1] == "yaml" :
        f = open(filename, 'r')
    elif filename.rsplit('.', 1)[1] == "bz2":
        f = BZ2File(filename)
    else:
        return

    next_scalar_type = "key"
    station = None
    attKey = None
    attValue = None
    for ev in yaml.parse(f):
        if isinstance(ev, MappingStartEvent):
            # 1 mapping per station
            station = Station() # create new station
            next_scalar_type = "key"
        elif isinstance(ev, ScalarEvent):
            if next_scalar_type == "key":
                attKey = ev.value
                next_scalar_type = "value"
            elif next_scalar_type == "value":
                attValue = ev.value
                if attKey == "stationName":
                    station.stationName = attValue
                elif attKey == "stationID":
                    station.stationID = long(attValue)
                next_scalar_type = "key"
        elif isinstance(ev, MappingEndEvent):
            # write it
            db.session.merge(station)
    
    db.session.commit()
    
    f.close()

def update_constellations(filename):
    if not path.isfile(filename):
        return
    con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute("SELECT constellationID, constellationName FROM mapConstellations")
    rows = cur.fetchmany()
    while len(rows) > 0:
        for row in rows:
            const = Constellation()
            const.constellationID = row[0]
            const.constellationName = row[1]
            db.session.merge(const)
        rows = cur.fetchmany()
    
    con.close()
    
    db.session.commit()
    
def update_systems(filename):
    if not path.isfile(filename):
        return
    con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute("SELECT solarSystemID, solarSystemName FROM mapSolarSystems")
    rows = cur.fetchmany()
    while len(rows) > 0:
        for row in rows:
            system = SolarSystem()
            system.solarSystemID = row[0]
            system.solarSystemName = row[1]
            db.session.merge(system)
        rows = cur.fetchmany()
    
    con.close()
    
    db.session.commit()

def update_layouts(filename):
    key_const = "Constellation"
    #key_staging = "Staging System"
    key_hq = "Headquarter System"
    key_dock = "Dockup"
    if not path.isfile(filename):
        return

    if filename.rsplit('.', 1)[1] == "csv" :
        f = open(filename, 'r')
    elif filename.rsplit('.', 1)[1] == "bz2":
        f = BZ2File(filename)
    else:
        return

    reader = csv.DictReader(f, delimiter="\t", quotechar='\\')
    for row in reader:
        constellation = db.session.query(Constellation).filter(Constellation.constellationName == row[key_const]).first()
        if constellation == None:
            continue
        #staging = db.session.query(SolarSystem).filter(SolarSystem.solarSystemName == row[key_staging]).first()
        hq = db.session.query(SolarSystem).filter(SolarSystem.solarSystemName == row[key_hq]).first()
        dock = db.session.query(Station).filter(Station.stationName == row[key_dock]).first()
        if hq == None or dock == None:
            continue
        
        inc_const = IncursionLayout()
        inc_const.constellation = constellation.constellationID
        #inc_const.staging = staging.solarSystemID
        inc_const.headquarter = hq.solarSystemID
        inc_const.dockup = dock.stationID
        db.session.merge(inc_const)

    f.close()
    db.session.commit()