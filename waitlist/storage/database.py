from sqlalchemy import Column, Integer, String, SmallInteger, BIGINT, Boolean, DateTime, Index,\
    sql, BigInteger
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Table, ForeignKey
from sqlalchemy.dialects.mysql.base import LONGTEXT, TEXT
import bcrypt
import logging
from waitlist.base import db
from datetime import datetime
from waitlist.utility.utils import get_random_token

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

backseats = Table("backseats",
                  Base.metadata,
                  Column("accountID", Integer, ForeignKey('accounts.id', ondelete="CASCADE")),
                  Column("groupID", Integer, ForeignKey('waitlist_groups.groupID', ondelete="CASCADE"))
                  )
fcs = Table("fcs",
            Base.metadata,
            Column("accountID", Integer, ForeignKey('accounts.id', ondelete="CASCADE")),
            Column("groupID", Integer, ForeignKey('waitlist_groups.groupID', ondelete="CASCADE"))
            )
fmanager = Table("fleetmanager",
                 Base.metadata,
                 Column("accountID", Integer, ForeignKey('accounts.id', ondelete="CASCADE")),
                 Column("groupID", Integer, ForeignKey('waitlist_groups.groupID', ondelete="CASCADE"))
            )

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

class MarketGroup(Base):
    __tablename__ = 'invmarketgroups'
    marketGroupID = Column(Integer, primary_key=True, nullable=False)
    parentGroupID = Column(Integer, ForeignKey('invmarketgroups.marketGroupID'))
    marketGroupName = Column(String(100))
    description = Column(String(3000))
    iconID = Column(Integer)
    hasTypes = Column(Boolean)

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
    login_token = Column(String(16), unique=True)
    disabled = Column(Boolean, default=False, server_default=sql.expression.false())
    refresh_token = Column(String(128), default=None)
    access_token = Column(String(128), default=None)
    access_token_expires = Column(DateTime, default=datetime.utcnow)

    roles = relationship('Role', secondary=roles,
                         backref=backref('account_roles'))
    characters = relationship('Character', secondary=linked_chars,
                              backref=backref('linked_chars'))
    current_char_obj = relationship('Character')

    fleet = relationship('CrestFleet', uselist=False, back_populates="comp")
    
    @property
    def lc_level(self):
        return self.current_char_obj.lc_level
    
    @lc_level.setter
    def lc_level(self, val):
        self.current_char_obj.lc_level = val
    
    @property
    def cbs_level(self):
        return self.current_char_obj.cbs_level
    
    @cbs_level.setter
    def cbs_level(self, val):
        self.current_char_obj.cbs_level = val
    
    def get_eve_name(self):
        return self.current_char_obj.eve_name
    
    def get_eve_id(self):
        return self.current_char

    def is_new(self):
        return self.current_char_obj.is_new()

    @property
    def type(self):
        return "account"
    
    @property
    def poke_me(self):
        return self.current_char_obj.poke_me
    
    @poke_me.setter
    def poke_me(self, value):
        self.current_char_obj.poke_me = value
    
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

class CrestFleet(Base):
    ''' Represents a setup fleet '''
    __tablename__ = 'crest_fleets'
    
    fleetID = Column(BigInteger, primary_key=True)
    logiWingID = Column(BigInteger)
    logiSquadID = Column(BigInteger)
    sniperWingID = Column(BigInteger)
    sniperSquadID = Column(BigInteger)
    dpsWingID = Column(BigInteger)
    dpsSquadID = Column(BigInteger)
    otherWingID = Column(BigInteger)
    otherSquadID = Column(BigInteger)
    groupID = Column(Integer, ForeignKey('waitlist_groups.groupID'), nullable=False)
    compID = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    group = relationship("WaitlistGroup", uselist=False, back_populates="fleets")
    comp = relationship("Account", uselist=False, back_populates="fleet")

class Character(Base):
    """
    Represents a eve character by its id
    """
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True)
    eve_name = Column(String(100))
    newbro = Column(Boolean, default=True, nullable=False)
    lc_level = Column(SmallInteger, default=0, nullable=False)
    cbs_level = Column(SmallInteger, default=0, nullable=False)
    login_token = Column(String(16), nullable=True)
    teamspeak_poke = Column(Boolean, default=True, server_default="1", nullable=False)

    def get_login_token(self):
        if self.login_token == None:
            self.login_token = get_random_token(16)
        return self.login_token
    
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
    
    @property
    def poke_me(self):
        return self.teamspeak_poke
    
    @poke_me.setter
    def poke_me(self, value):
        self.teamspeak_poke = value
    
    def __repr__(self):
        return "<Character id={0} eve_name={1}>".format(self.id, self.eve_name)

class Role(Base):
    '''
    Represents a role like, FleetCommander, Officer, LogisticsMaster, FC-Trainee, Resident
    '''
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    displayName = Column(String(150), unique=False)
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
    name = Column(String(50))
    groupID = Column(Integer, ForeignKey("waitlist_groups.groupID"))
    displayTitle = Column(String(100), nullable=False, default="")
    entries = relationship("WaitlistEntry", back_populates="waitlist", order_by="asc(WaitlistEntry.creation)")
    group = relationship("WaitlistGroup", uselist=False, foreign_keys=[groupID])

    def __repr__(self):
        return "<Waitlist %r>" % (self.name)

class WaitlistGroup(Base):
    """
    Represents a waitlist Group,
    A waitlist group always contains 1 x-up list
    and 3 approved lists for dps, 1 for sniper and 1 for logi
    and can contain an other one for out of line ships
    """
    
    __tablename__ = "waitlist_groups"
    
    groupID = Column(Integer, primary_key=True)
    groupName = Column(String(50), unique=True, nullable=False)
    displayName = Column(String(50), unique=True, nullable=False)
    xupwlID = Column(Integer, ForeignKey(Waitlist.id), nullable=False)
    logiwlID = Column(Integer, ForeignKey(Waitlist.id), nullable=False)
    dpswlID = Column(Integer, ForeignKey(Waitlist.id), nullable=False)
    sniperwlID = Column(Integer, ForeignKey(Waitlist.id), nullable=False)
    otherwlID = Column(Integer, ForeignKey(Waitlist.id), nullable=True)
    enabled = Column(Boolean, nullable=False, default=False)
    status = Column(String(1000), default="Down")
    dockupID = Column(Integer, ForeignKey(Station.stationID), nullable=True)
    systemID = Column(Integer, ForeignKey(SolarSystem.solarSystemID), nullable=True)
    constellationID = Column(Integer, ForeignKey(Constellation.constellationID), nullable=True)
    odering = Column(Integer, nullable=False, default=0)
    influence = Column(Boolean, nullable=False, server_default='0', default=False)
    
    xuplist = relationship("Waitlist", foreign_keys=[xupwlID])
    logilist = relationship("Waitlist", foreign_keys=[logiwlID])
    dpslist = relationship("Waitlist", foreign_keys=[dpswlID])
    sniperlist = relationship("Waitlist", foreign_keys=[sniperwlID])
    otherlist = relationship("Waitlist", foreign_keys=[otherwlID])
    dockup = relationship("Station", uselist=False)
    system = relationship("SolarSystem", uselist=False)
    constellation = relationship("Constellation", uselist=False)
    fleets = relationship("CrestFleet", back_populates="group")
    backseats = relationship("Account", secondary="backseats")
    fcs = relationship("Account", secondary="fcs")
    manager = relationship("Account", secondary="fleetmanager")

class Shipfit(Base):
    """
    Represents a single fit
    """
    __tablename__ = "fittings"
    
    id = Column(Integer, primary_key=True)
    ship_type = Column(Integer, ForeignKey("invtypes.typeID"))
    modules = Column(String(5000))
    comment = Column(String(5000))
    wl_type = Column(String(10))
    created = Column(DateTime, default=datetime.utcnow)
    
    ship = relationship("InvType")
    waitlist = relationship("WaitlistEntry", secondary="waitlist_entry_fits", uselist=False)
    
    def get_dna(self):
        return "{0}:{1}".format(self.ship_type, self.modules)
    
    def __repr__(self):
        return "<Shipfit id={0} ship_type={1} modules={2} comment={3} waitlist={4}>".format(self.id, self.ship_type, self.modules, self.comment, self.waitlist.id)

class WaitlistEntryFit(Base):
    __tablename__ = "waitlist_entry_fits"
    entryID = Column(Integer, ForeignKey("waitlist_entries.id", onupdate="CASCADE", ondelete="CASCADE"))
    fitID = Column(Integer, ForeignKey("fittings.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)

class WaitlistEntry(Base):
    """
    Represents a person in a waitlist_id
    A person in a waitlist_id always needs to have a user(his character) and and one or more fits
    """
    __tablename__ = "waitlist_entries"
    id = Column(Integer, primary_key=True)
    creation = Column(DateTime)
    user = Column(Integer, ForeignKey('characters.id'))
    fittings = relationship("Shipfit", secondary="waitlist_entry_fits")
    waitlist_id = Column(Integer, ForeignKey("waitlists.id", onupdate="CASCADE", ondelete="CASCADE"))
    timeInvited = Column(DateTime, default=None)
    inviteCount = Column(Integer, default=0)
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
    name = Column(String(100))
    
class APICacheCharacterInfo(Base):
    __tablename__ = "apicache_characterinfo"
    id = Column(Integer, primary_key=True)
    corporationID = Column(Integer, index=True)
    corporationName = Column(String(100))
    expire = Column(DateTime)

class APICacheCorporationInfo(Base):
    __tablename__ = "apicache_corporationinfo"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True)
    allianceID = Column(Integer, index=True)
    allianceName = Column(String(100), index=True)
    expire = Column(DateTime)

class APICacheCharacterAffiliation(Base):
    __tablename__ = "apicache_characteraffiliation"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True)
    corporationID = Column(Integer, index=True)
    corporationName = Column(String(100), index=True)
    allianceID = Column(Integer, index=True)
    allianceName = Column(String(100), index=True)
    expire = Column(DateTime)

class Ban(Base):
    __tablename__ = "ban"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True)
    reason = Column(TEXT)
    admin = Column(Integer, ForeignKey("characters.id"))
    admin_obj = relationship("Character", foreign_keys="Ban.admin")

class Whitelist(Base):
    __tablename__ = "whitelist"
    characterID = Column(Integer, ForeignKey(Character.id), primary_key=True)
    reason = Column(TEXT)
    adminID = Column(Integer, ForeignKey(Character.id))
    character = relationship(Character, foreign_keys=[characterID])
    admin = relationship(Character, foreign_keys=[adminID])

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

class Ticket(Base):
    """
    Contains a single 'feedback' entry from a linemember, which can have states
    """
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    characterID = Column(Integer, ForeignKey('characters.id'), index=True)
    message = Column(TEXT)
    state = Column(String(20), nullable=False, index=True, default="new")
    
    character = relationship("Character")

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

class HistoryFits(Base):
    __tablename__ = "comp_history_fits"
    id = Column(Integer, primary_key=True)
    historyID = Column(Integer, ForeignKey("comp_history.historyID"))
    fitID = Column(Integer, ForeignKey("fittings.id"))

class HistoryEntry(Base):
    __tablename__ = "comp_history"
    historyID = Column(Integer, primary_key=True)
    sourceID = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    targetID = Column(Integer, ForeignKey("characters.id"), nullable=False)
    action = Column(String(20))
    time = Column(DateTime, default=datetime.utcnow, index=True)
    exref = Column(Integer, nullable=True, default=None)
    fittings = relationship("Shipfit", secondary="comp_history_fits")
    source = relationship("Account")
    target = relationship("Character")
    
    EVENT_XUP = "xup"
    EVENT_COMP_RM_PL = "comp_rm_pl"
    EVENT_COMP_INV_PL = "comp_inv_pl"
    EVENT_COMP_NOTI_PL = "comp_send_noti"
    EVENT_COM_RM_ETR = "comp_rm_etr"
    EVENT_SELF_RM_FIT = "self_rm_fit"
    EVENT_SELF_RM_ETR = "self_rm_etr"
    EVENT_SELF_RM_WLS_ALL = "self_rm_wls_all"
    EVENT_COMP_MV_XUP_ETR = "comp_mv_xup_etr"
    EVENT_COMP_MV_XUP_FIT = "comp_mv_xup_fit"
    EVENT_AUTO_RM_PL = "auto_rm_pl"
    EVENT_AUTO_CHECK_FAILED = "auto_inv_missed"
    EVENT_COMP_INV_BY_NAME = "comp_inv_by_name"


class HistoryExtInvite(Base):
    __tablename__ = "comp_history_ext_inv"
    inviteExtID = Column(Integer, primary_key=True)
    historyID = Column(Integer, ForeignKey(HistoryEntry.historyID))
    waitlistID = Column(Integer, ForeignKey(Waitlist.id))
    timeCreated = Column(DateTime)
    timeInvited = Column(DateTime)

class EventHistoryType(Base):
    __tablename__ = "event_history_types"
    typeID = Column(Integer, primary_key=True)
    typeName = Column(String(20), unique=True)

class EventHistoryEntry(Base):
    __tablename__ = "event_history_entries"
    historyID = Column(Integer, primary_key=True)
    time = Column(DateTime, default=datetime.utcnow, index=True)
    typeID = Column(Integer, ForeignKey("event_history_types.typeID"))

    type = relationship("EventHistoryType", uselist=False)

class EventHistoryInfo(Base):
    __tablename__ = "event_history_info"
    infoID = Column(Integer, primary_key=True)
    historyID = Column(Integer, ForeignKey("event_history_entries.historyID"))
    infoType = Column(Integer)
    referenceID = Column(Integer)

class TeamspeakDatum(Base):
    __tablename__ = "ts_dati"
    teamspeakID = Column(Integer, primary_key=True)
    displayName = Column(String(128)) # this is displayed in menus and such
    host = Column(String(128)) # for internal connection
    port = Column(Integer) # for internal connection
    displayHost = Column(String(128)) # this should be shown to public
    displayPort = Column(Integer) # this should be shown to public
    queryName = Column(String(128))
    queryPassword = Column(String(128))
    serverID = Column(Integer)
    channelID = Column(Integer)
    clientName = Column(String(20))
    safetyChannelID = Column(Integer)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(20), primary_key=True)
    value = Column(TEXT)

class RoleHistoryEntry(Base):
    __tablename__ = "role_history"
    entryID = Column(Integer, primary_key=True)
    accountID = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    byAccountID = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    note = Column(TEXT, nullable=True)
    time = Column(DateTime, default=datetime.utcnow, index=True)
    role_changes = relationship("RoleChangeEntry", back_populates="history_entry", order_by="desc(RoleChangeEntry.added)")

class RoleChangeEntry(Base):
    __tablename__ = "role_changes"
    roleChangeID = Column(Integer, primary_key=True)
    entryID = Column(Integer, ForeignKey('role_history.entryID', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    roleID = Column(Integer, ForeignKey('roles.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    added = Column(Boolean, nullable=False)
    history_entry = relationship("RoleHistoryEntry", back_populates="role_changes")
    role = relationship('Role')
