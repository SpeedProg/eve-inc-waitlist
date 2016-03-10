import yaml
from os import path
from waitlist import db
from yaml.events import MappingStartEvent, ScalarEvent, MappingEndEvent
import time
from bz2 import BZ2File
import csv
from waitlist.storage.database import Station, InvType, Constellation,\
    SolarSystem
import sqlite3

def update_invtypes():
    # this might be better off writing a specific parser for performance, yaml is really slow
    inv_type = None
    att_name = None
    subatt_name = None
    mapping_count = 0
    is_normal = True
    filename = path.join(".", "sde", "typeIDs.yaml")
    if not path.isfile(filename):
        is_normal = False
    else:
        filename = path.join(".", "sde", "typeIDs.yaml.bz2")
        if not path.isfile(filename):
            return
    
    if is_normal:
        f = open(filename, 'r')
    else:
        f = BZ2File(filename)

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
                        #print "set group id "+ str(inv_type.groupID)
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
                #print ">>end subattr mapping"
                att_name = None
                subatt_name = None
            elif mapping_count == 2:
                #print ">end attr mapping"
                att_name = None
                add_invtype_to_db(inv_type)
            #elif mapping_count == 1:
                #print "end inv mapping"
            mapping_count -= 1
    
    if (is_normal):
        f.close()
    db.session.commit()
    db.session.close()

def add_invtype_to_db(inv_type):
    db.session.merge(inv_type)

def update_stations():
    filename = path.join(".", "sde", "staStations.csv.bz2")
    if not path.isfile(filename):
        return
    with BZ2File(filename) as stationfile:
        reader = csv.DictReader(stationfile, delimiter=',', quotechar='\\')
        for row in reader:
            station = Station()
            station.stationID = row['stationID']
            station.stationName = row['stationName']
            update_or_add_station(station)
    
    db.session.commit()

def update_or_add_station(station):
    db.session.merge(station)

def update_constellations():
    filename = path.join(".", "sde", "universeDataDx.db")
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
            update_or_add_constellation(const)
        rows = cur.fetchmany()
    
    con.close()
    
    db.session.commit()

def update_or_add_constellation(const):
    db.session.merge(const)
   
def update_systems():
    filename = path.join(".", "sde", "universeDataDx.db")
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
            update_or_add_system(system)
        rows = cur.fetchmany()
    
    con.close()
    
    db.session.commit()

def update_or_add_system(system):
    db.session.merge(system)

if __name__ == '__main__':
    start = time.time()
    update_counter = 0
    update_invtypes()
    start_station = time.time()
    print("Invtypes: " + str(start_station-start))
    update_stations()
    start_const = time.time()
    print("Stations: " + str(start_const - start_station))
    update_constellations()
    start_system = time.time()
    print("Constellations: " + str(start_system - start_const))
    update_systems()
    end = time.time()
    print("Systems: "+ str(end - start_system))
    print("Sum: "+ str((end-start)/60) + "min")
    
    
