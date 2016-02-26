from sqlalchemy import Column, Integer, String, SmallInteger,\
    DECIMAL, BIGINT, Boolean, DateTime
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Table, ForeignKey
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.dialects.mysql.base import LONGTEXT, DOUBLE, TINYINT
import bcrypt

dbpath = "tmp//test.db"
user = "wtm"
password = "wtm"
host = "localhost"
port = 3306
dbname = "wtm"
dbstring = "mysql+mysqldb://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, dbname)
engine = create_engine(dbstring, echo=False)
conn = engine.connect()

#existing_metadata = MetaData()
#existing_metadata.reflect(engine, only=["invtypes"])

#AutoBase = automap_base(metadata=existing_metadata)
#AutoBase.prepare()

Base = declarative_base() #declarative_base(metadata=existing_metadata)


"""
typeID = id of module
typeName = name of module
"""
#Module = AutoBase.classes.invtypes

roles = Table('account_roles',
              Base.metadata,
              Column('account_id', Integer, ForeignKey('accounts.id')),
              Column('role_id', Integer, ForeignKey('roles.id'))
              )

linked_chars = Table('linked_chars',
                     Base.metadata,
                     Column('id', Integer, ForeignKey('accounts.id')),
                     Column('char_id', Integer, ForeignKey('characters.id'))
                     )

class InvType(Base):
    __tablename__ = 'invtypes'
    
    typeID = Column(Integer, primary_key=True, nullable=False)
    groupID = Column(Integer)
    typeName = Column(String(100))
    description = Column(LONGTEXT)
    mass = Column(DOUBLE)
    volume = Column(DOUBLE)
    capacity = Column(DOUBLE)
    portionSize = Column(Integer)
    raceID = Column(SmallInteger)
    basePrice = Column(DECIMAL(19,4))
    published = Column(TINYINT)
    marketGroupID = Column(BIGINT)
    iconID = Column(BIGINT)
    soundID = Column(BIGINT)

class Account(Base):
    '''
    Represents a user
    '''    
    
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    set_character = Column(Integer, ForeignKey("characters.id"))
    username = Column(String(100), unique=True)# login name
    password = Column(String(100))
    email = Column(String(100), unique=True)
    login_token = Column(String(64), unique=True)
    roles = relationship('Role', secondary=roles,
                         backref=backref('roles'))
    characters = relationship('Character', secondary=linked_chars,
                              backref=backref('linked_chars'))
    
    def get_eve_id(self):
        return self.set_character

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
    newbro = Column(Boolean)

    def get_eve_id(self):
        return self.id

    @property
    def type(self):
        return "character"

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
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
    entries = relationship("WaitlistEntry", back_populates="waitlists")
    
    def __repr__(self):
        return "<Waitlist %r>" % (self.name)

fitted_modules = Table('fitted_modules',
                       Base.metadata,
                       Column('fit', Integer, ForeignKey('fittings.id')),
                       Column('module', Integer, ForeignKey('invtypes.typeID'))
                       )

class Shipfit(Base):
    """
    Represents a single fit
    """
    __tablename__ = "fittings"
    
    id = Column(Integer, primary_key=True)
    ship_type = Column(Integer, ForeignKey("invtypes.typeID"))
    waitlist = Column(Integer, ForeignKey('waitlist_entries.id'))
    modules = Column(String(200))
    comment = Column(String(200))
    
    def get_dna(self):
        return "{0}:{1}".format(self.ship_type, self.modules)
    
    def __repr__(self):
        return "<Shipfit id={0} ship_type={1} modules={2} comment={3} waitlist={4}>".format(self.id, self.ship_type, self.modules, self.comment, self.waitlist)


class WaitlistEntry(Base):
    """
    Represents a person in a waitlist
    A person in a waitlist always needs to have a user(his character) and and one or more fits
    """
    __tablename__ = "waitlist_entries"
    id = Column(Integer, primary_key=True)
    creation = Column(DateTime)
    user = Column(Integer, ForeignKey('characters.id'))
    fittings = relationship("Shipfit")
    waitlist = Column(Integer, ForeignKey("waitlists.id"))
    waitlists = relationship("Waitlist", back_populates="entries")


    def __repr__(self):
        return "<WaitlistEntry %r>" % (self.id)
    
Base.metadata.create_all(engine)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

def get_item_id(name):
    return session.query(InvType).filter(InvType.typeName == name).first().typeID