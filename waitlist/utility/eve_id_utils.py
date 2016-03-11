from waitlist.storage.database import Constellation, SolarSystem, Station
from waitlist import db
def get_constellation(name):
    return db.session.query(Constellation).filter(Constellation.constellationName == name).first()

def get_system(name):
    return db.session.query(SolarSystem).filter(SolarSystem.solarSystemName == name).first()

def get_station(name):
    return db.session.query(Station).filter(Station.stationName == name).first()