from sqlalchemy import Column, Integer, String, SmallInteger,\
    DECIMAL, BIGINT, Boolean, DateTime, Index
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Table, ForeignKey
from sqlalchemy.dialects.mysql.base import LONGTEXT, DOUBLE, TINYINT, TEXT
import bcrypt
import logging
from waitlist import db

logger = logging.getLogger(__name__)

#existing_metadata = MetaData()
#existing_metadata.reflect(engine, only=["invtypes"])

#AutoBase = automap_base(metadata=existing_metadata)
#AutoBase.prepare()

Base = db.Model


"""
typeID = id of module
typeName = name of module
"""
#Module = AutoBase.classes.invtypes

roles = Table('account_roles',
              Base.metadata,
              Column('account_id', Integer, ForeignKey('accounts.id', onupdate="CASCADE", ondelete="CASCADE")),
              Column('role_id', Integer, ForeignKey('roles.id', onupdate="CASCADE", ondelete="CASCADE"))
              )

linked_chars = Table('linked_chars',
                     Base.metadata,
                     Column('id', Integer, ForeignKey('accounts.id', onupdate="CASCADE", ondelete="CASCADE")),
                     Column('char_id', Integer, ForeignKey('characters.id', onupdate="CASCADE", ondelete="CASCADE"))
                     )

class InvType(Base):
    __tablename__ = 'invtypes'
    
    typeID = Column(Integer, primary_key=True, nullable=False)
    groupID = Column(Integer)
    typeName = Column(String(100))
    description = Column(LONGTEXT)
#    mass = Column(DOUBLE)
#    volume = Column(DOUBLE)
#    capacity = Column(DOUBLE)
#    portionSize = Column(Integer)
#    raceID = Column(SmallInteger)
#    basePrice = Column(DECIMAL(19,4))
#    published = Column(TINYINT)
    marketGroupID = Column(BIGINT)
#    iconID = Column(BIGINT)
#    soundID = Column(BIGINT)
    __table_args__ = (Index('invTypes_groupid', "groupID"),)

class Account(Base):
    '''
    Represents a user
    '''    
    
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    current_char = Column(Integer, ForeignKey("characters.id"))
    username = Column(String(100), unique=True)# login name
    password = Column(String(100))
    email = Column(String(100), unique=True)
    login_token = Column(String(64), unique=True)
    roles = relationship('Role', secondary=roles,
                         backref=backref('account_roles'))
    characters = relationship('Character', secondary=linked_chars,
                              backref=backref('linked_chars'))
    current_char_obj = relationship('Character')
    
    def get_eve_name(self):
        return self.current_char_obj.eve_name
    
    def get_eve_id(self):
        return self.current_char

    def is_new(self):
        return self.current_char_obj.is_new()

    @property
    def type(self):
        return "account"
    
    # check if password matches
    def password_match(self, pwd):
        if bcrypt.hashpw(self.pwd, self.password) == self.password:
            return True
        return False
    
    def token_match(self, token):
        if self.login_token == token:
            return True
        return False

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def get_id(self):
        return unicode("acc"+unicode(self.id))
    
    def set_password(self, pwd):
        self.password = bcrypt.hashpw(pwd, bcrypt.gensalt())
    
    def __repr__(self):
        return '<Account %r>' % (self.username)
    
class Character(Base):
    """
    Represents a eve character by its id
    """
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True)
    eve_name = Column(String(100), unique=True)
    newbro = Column(Boolean, default=True, nullable=False)

    def get_eve_name(self):
        return self.eve_name

    def get_eve_id(self):
        return self.id
    
    def is_new(self):
        return self.newbro

    @property
    def banned(self):
        return (db.session.query(Ban).filter(Ban.id == self.id).count() == 1)

    @property
    def type(self):
        return "character"

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return not self.banned
    
    def get_id(self):
        return unicode("char"+unicode(self.id))
    
    def __repr__(self):
        return "<Character id={0} eve_name={1}>".format(self.id, self.eve_name)
    
class Role(Base):
    '''
    Represents a role like, FleetCommander, Officer, LogisticsMaster, FC-Trainee, Resident
    '''
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    # if this = 1 and some one has this role, he can not login by igb header
    is_restrictive = Column(Integer)

    def __repr__(self):
        return "<Role %r>" % (self.name)

class Waitlist(Base):
    """
    Represents a waitlist
    """
    __tablename__ = 'waitlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True)
    entries = relationship("WaitlistEntry", back_populates="waitlist", order_by="asc(WaitlistEntry.creation)")
    
    def __repr__(self):
        return "<Waitlist %r>" % (self.name)

class Shipfit(Base):
    """
    Represents a single fit
    """
    __tablename__ = "fittings"
    
    id = Column(Integer, primary_key=True)
    ship_type = Column(Integer, ForeignKey("invtypes.typeID"))
    ship = relationship("InvType")
    waitlist_id = Column(Integer, ForeignKey('waitlist_entries.id', onupdate="CASCADE", ondelete="CASCADE"))
    modules = Column(String(10000))
    comment = Column(String(10000))
    wl_type = Column(String(10))
    
    def get_dna(self):
        return "{0}:{1}".format(self.ship_type, self.modules)
    
    def __repr__(self):
        return "<Shipfit id={0} ship_type={1} modules={2} comment={3} waitlist_id={4}>".format(self.id, self.ship_type, self.modules, self.comment, self.waitlist_id)


class WaitlistEntry(Base):
    """
    Represents a person in a waitlist_id
    A person in a waitlist_id always needs to have a user(his character) and and one or more fits
    """
    __tablename__ = "waitlist_entries"
    id = Column(Integer, primary_key=True)
    creation = Column(DateTime)
    user = Column(Integer, ForeignKey('characters.id'))
    fittings = relationship("Shipfit", cascade="save-update,merge,delete")
    waitlist_id = Column(Integer, ForeignKey("waitlists.id", onupdate="CASCADE", ondelete="CASCADE"))
    waitlist = relationship("Waitlist", back_populates="entries")
    user_data = relationship("Character")

    def __repr__(self):
        return "<WaitlistEntry %r>" % (self.id)

class APICacheCharacterID(Base):
    """
    Maps Character Names and IDs
    """
    __tablename__ = "apicache_characterid"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    
class APICacheCharacterInfo(Base):
    __tablename__ = "apicache_characterinfo"
    id = Column(Integer, primary_key=True)
    corporationID = Column(Integer, index=True)
    corporationName = Column(String(100))
    expire = Column(DateTime)

class APICacheCorporationInfo(Base):
    __tablename__ = "apicache_corporationinfo"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True, unique=True)
    allianceID = Column(Integer, index=True)
    allianceName = Column(String(100), index=True)
    expire = Column(DateTime)

class APICacheCharacterAffiliation(Base):
    __tablename__ = "apicache_characteraffiliation"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True, unique=True)
    corporationID = Column(Integer, index=True)
    corporationName = Column(String(100), index=True)
    allianceID = Column(Integer, index=True)
    allianceName = Column(String(100), index=True)
    expire = Column(DateTime)

class Ban(Base):
    __tablename__ = "ban"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True, unique=True)
    reason = Column(TEXT)
    admin = Column(Integer, ForeignKey("characters.id"))
    admin_obj = relationship("Character", foreign_keys="Ban.admin")

class Feedback(Base):
    """
    Contains the feedback people give about the waitlist
    """
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    last_changed = Column(DateTime, index=True)
    user = Column(Integer, ForeignKey('characters.id'), unique=True, index=True)
    user_data = relationship("Character")
    likes = Column(Boolean)
    comment = Column(TEXT)

class Station(Base):
    __tablename__ = "station"
    stationID = Column(Integer, primary_key=True)
    stationName = Column(String(100), index=True, unique=True)

class SolarSystem(Base):
    __tablename__ = "solarsystem"
    solarSystemID = Column(Integer, primary_key=True)
    solarSystemName = Column(String(100), index=True, unique=True)

class Constellation(Base):
    __tablename__ = "constellation"
    constellationID = Column(Integer, primary_key=True)
    constellationName = Column(String(100), index=True, unique=True)

class IncursionLayout(Base):
    __tablename__ = "incursion_layout"
    constellation = Column(Integer, ForeignKey("constellation.constellationID"), primary_key=True)
    staging = Column(Integer, ForeignKey("solarsystem.solarSystemID"))
    headquarter = Column(Integer, ForeignKey("solarsystem.solarSystemID"))
    dockup = Column(Integer, ForeignKey("station.stationID"))
    
    obj_constellation = relationship("Constellation", foreign_keys="IncursionLayout.constellation")
    obj_staging= relationship("SolarSystem", foreign_keys="IncursionLayout.staging")
    obj_headquarter = relationship("SolarSystem", foreign_keys="IncursionLayout.headquarter")
    obj_dockup = relationship("Station", foreign_keys="IncursionLayout.dockup")
    
