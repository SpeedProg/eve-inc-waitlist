from typing import List, Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, SmallInteger, BIGINT, Boolean, DateTime, Index, \
    sql, BigInteger, text, Float, Text
from sqlalchemy import Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Table, ForeignKey, CheckConstraint, UniqueConstraint
import logging

from waitlist import db
from datetime import datetime
from waitlist.utility.utils import get_random_token

logger = logging.getLogger(__name__)

# existing_metadata = MetaData()
# existing_metadata.reflect(engine, only=["invtypes"])

# AutoBase = automap_base(metadata=existing_metadata)
# AutoBase.prepare()

Base = db.Model

"""
typeID = id of module
typeName = name of module
"""
# Module = AutoBase.classes.invtypes

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
                  Column("account_id", Integer, ForeignKey('accounts.id', ondelete="CASCADE")),
                  Column("group_id", Integer, ForeignKey('waitlist_groups.group_id', ondelete="CASCADE"))
                  )

fcs = Table("fcs",
            Base.metadata,
            Column("account_id", Integer, ForeignKey('accounts.id', ondelete="CASCADE")),
            Column("group_id", Integer, ForeignKey('waitlist_groups.group_id', ondelete="CASCADE"))
            )

fmanager = Table("fleetmanager",
                 Base.metadata,
                 Column("account_id", Integer, ForeignKey('accounts.id', ondelete="CASCADE")),
                 Column("group_id", Integer, ForeignKey('waitlist_groups.group_id', ondelete="CASCADE"))
                 )


class EveApiScope(Base):
    __tablename__ = 'eveapiscope'
    tokenID = Column('token_id', Integer, ForeignKey('ssotoken.character_id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    scopeName = Column('scope_name', String(100), primary_key=True)


class SSOToken(Base):
    __tablename__ = 'ssotoken'
    characterID = Column('character_id', Integer, ForeignKey('characters.id', onupdate="CASCADE", ondelete="CASCADE"),
                         primary_key=True)
    # the last account that used this char, if null means no account=>standalone char
    accountID = Column('account_id', Integer, ForeignKey('accounts.id', onupdate="CASCADE", ondelete="CASCADE"),
                       nullable=True)
    refresh_token = Column('refresh_token', String(128), default=None)
    access_token = Column('access_token', String(128), default=None)
    access_token_expires = Column('access_token_expires', DateTime, default=datetime.utcnow)

    scopes:List[EveApiScope] = relationship(EveApiScope, cascade="save-update, merge, delete, delete-orphan")


class Station(Base):
    __tablename__ = "station"
    stationID = Column('station_id', Integer, primary_key=True)
    stationName = Column('station_name', String(100), index=True, unique=True)


class SolarSystem(Base):
    __tablename__ = "solarsystem"
    solarSystemID = Column('solar_system_id', Integer, primary_key=True)
    solarSystemName = Column('solar_system_name', String(100), index=True, unique=True)


class Constellation(Base):
    __tablename__ = "constellation"
    constellationID = Column('constellation_id', Integer, primary_key=True)
    constellationName = Column('constellation_name', String(100), index=True, unique=True)


class InvType(Base):
    __tablename__ = 'invtypes'
    typeID = Column('type_id', Integer, primary_key=True, nullable=False)
    groupID = Column('group_id', Integer, index=True)
    typeName = Column('type_name', String(100))
    description = Column('description', Text)
    #    mass = Column(DOUBLE)
    #    volume = Column(DOUBLE)
    #    capacity = Column(DOUBLE)
    #    portionSize = Column(Integer)
    #    raceID = Column(SmallInteger)
    #    basePrice = Column(DECIMAL(19,4))
    #    published = Column(TINYINT)
    marketGroupID = Column('market_group_id', BIGINT)
    #    iconID = Column(BIGINT)
    #    soundID = Column(BIGINT)

    def __repr__(self):
        return f'<InvType typeID={self.typeID} typeName={self.typeName} groupID={self.groupID}' \
               f' marketGroupID={self.marketGroupID} description={self.description}>'



class MarketGroup(Base):
    __tablename__ = 'invmarketgroups'
    marketGroupID = Column('market_group_id', Integer, primary_key=True, nullable=False)
    parentGroupID = Column('parent_group_id', Integer, ForeignKey('invmarketgroups.market_group_id'))
    marketGroupName = Column('market_group_name', String(100))
    description = Column('description', String(3000))
    iconID = Column('icon_id', Integer)
    hasTypes = Column('has_types', Boolean(name='has_types'))


class Account(Base):
    """
    Represents a user
    """

    __tablename__ = 'accounts'

    id = Column('id', Integer, primary_key=True)
    # the session key is used to invalidate old sessions by chaning it
    # if id + session_key does not match the session is invalid
    session_key = Column('session_key', Integer, nullable=False, server_default='0')
    current_char = Column('current_char', Integer, ForeignKey("characters.id"))
    username = Column('username', String(100), unique=True)  # login name
    login_token = Column('login_token', String(16), unique=True)
    disabled = Column('disabled', Boolean(name='disabled'), default=False, server_default=sql.expression.false())
    had_welcome_mail = Column('had_welcome_mail', Boolean(name='had_welcome_mail'), default=False, server_default=sql.expression.false())
    '''
    refresh_token = Column(String(128), default=None)
    access_token = Column(String(128), default=None)
    access_token_expires = Column(DateTime, default=datetime.utcnow)
    '''
    roles = relationship('Role', secondary=roles,
                         backref=backref('account_roles'))
    characters = relationship('Character', secondary=linked_chars,
                              back_populates='accounts')
    current_char_obj = relationship('Character')

    fleet = relationship('CrestFleet', uselist=False, back_populates="comp")

    ssoTokens: List[SSOToken] = relationship('SSOToken')

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
    def owner_hash(self):
        if self.current_char is None:
            return None
        return self.current_char_obj.owner_hash

    @property
    def type(self):
        return "account"

    @property
    def poke_me(self) -> bool:
        return self.current_char_obj.poke_me

    @poke_me.setter
    def poke_me(self, value: bool):
        self.current_char_obj.poke_me = value

    @property
    def sso_token(self) -> Optional[SSOToken]:
        """
        Get the sso token for the currently active character
        :return: the SSOToken or None
        """
        for token in self.ssoTokens:
            if token.characterID == self.current_char_obj.id:
                return token

        return None

    @sso_token.setter
    def sso_token(self, value: SSOToken) -> None:
        """
        Set the token for the current active character on this account.
        :param value: the sso token
        :return: None
        """
        # lets check if there is a token for this character

        token: SSOToken = SSOToken.query.filter(SSOToken.characterID == self.current_char).one_or_none()
        # remove the old token
        if token is not None:
            db.session.delete(token)

        # add the token
        value.characterID = self.current_char_obj.id
        self.ssoTokens.append(value)


    # check if password matches
    # def password_match(self, pwd):
    #    if bcrypt.hashpw(self.pwd, self.password) == self.password:
    #       return True
    #   return False

    def token_match(self, token):
        if self.login_token == token:
            return True
        return False

    def is_authenticated(self):
        return not self.disabled

    def is_active(self):
        return not self.disabled

    def get_id(self):
        return "acc" + str(self.id) + '_' + str(self.session_key)

    # def set_password(self, pwd):
    #    self.password = bcrypt.hashpw(pwd, bcrypt.gensalt())

    def __repr__(self):
        return f'<Account {self.username} id={self.id} session_key={self.session_key}>'


class CrestFleet(Base):
    """ Represents a setup fleet """
    __tablename__ = 'crest_fleets'

    fleetID = Column('fleet_id', BigInteger, primary_key=True)
    logiWingID = Column('logi_wing_id', BigInteger)
    logiSquadID = Column('logi_squad_id', BigInteger)
    sniperWingID = Column('sniper_wing_id', BigInteger)
    sniperSquadID = Column('sniper_squad_id', BigInteger)
    dpsWingID = Column('dps_wing_id', BigInteger)
    dpsSquadID = Column('dps_squad_id', BigInteger)
    otherWingID = Column('other_wing_id', BigInteger)
    otherSquadID = Column('other_squad_id', BigInteger)
    groupID = Column('group_id', Integer, ForeignKey('waitlist_groups.group_id'), nullable=False)
    compID = Column('comp_id', Integer, ForeignKey("accounts.id"), nullable=True)

    group = relationship("WaitlistGroup", uselist=False, back_populates="fleets")
    comp = relationship("Account", uselist=False, back_populates="fleet")


class Character(Base):
    """
    Represents a eve character by its id
    """
    __tablename__ = "characters"

    id = Column('id', Integer, primary_key=True)
    # the session key is used to invalidate old sessions by chaning it
    # if id + session_key does not match the session is invalid
    session_key = Column('session_key', Integer, nullable=False, server_default='0')
    eve_name = Column('eve_name', String(100))
    newbro = Column('new_bro', Boolean(name='new_bro'), default=True, nullable=False)
    lc_level = Column('lc_level', SmallInteger, default=0, nullable=False)
    cbs_level = Column('cbs_level', SmallInteger, default=0, nullable=False)
    login_token = Column('login_token', String(16), nullable=True)
    teamspeak_poke = Column('teamspeak_poke', Boolean(name='teamspeak_poke'), default=True, server_default="1", nullable=False)
    owner_hash = Column('owner_hash', Text)

    # this contains all SSOToken for this character
    # normally we only want the ones not associated with an account! we got a property for this
    ssoTokens: List[SSOToken] = relationship('SSOToken')

    accounts = relationship(
        "Account",
        secondary=linked_chars,
        back_populates="characters")

    @property
    def sso_token(self) -> Optional[SSOToken]:
        """
        Get the SSOToken for this character without account
        :return: the SSOToken
        """
        for token in self.ssoTokens:
            if token.accountID is None:
                return token

        return None

    @sso_token.setter
    def sso_token(self, value: SSOToken) -> None:
        """
        Set the token for the current character as none Account token
        :param value: the sso token
        :return: None
        """

        token: SSOToken = SSOToken.query.filter(SSOToken.characterID == self.id).one_or_none()
        # remove the old token
        if token is not None:
            db.session.delete(token)

        # add the token
        value.characterID = self.id
        value.accountID = None
        self.ssoTokens.append(value)

    def get_login_token(self):
        if self.login_token is None:
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
        return db.session.query(Ban).filter(Ban.id == self.id).count() == 1

    @property
    def type(self):
        return "character"

    @classmethod
    def is_authenticated(cls):
        return True

    def is_active(self):
        return not self.banned

    def get_id(self):
        return "char" + str(self.id) + '_' + str(self.session_key)

    @property
    def poke_me(self):
        return self.teamspeak_poke

    @poke_me.setter
    def poke_me(self, value):
        self.teamspeak_poke = value

    def __repr__(self):
        return f'<Character {self.eve_name} id={self.id} session_key={self.session_key}>'


class Role(Base):
    """
    Represents a role like, FleetCommander, Officer, LogisticsMaster, FC-Trainee, Resident
    """
    __tablename__ = 'roles'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(50), unique=True)
    displayName = Column('display_name', String(150), unique=False)

    def __repr__(self):
        return "<Role %r>" % self.name


permission_roles = Table('permission_roles', Base.metadata,
                         Column('permission', Integer, ForeignKey('permissions.id')),
                         Column('role', Integer, ForeignKey(Role.id))
                         )


class Permission(Base):
    """
    Represents a permission like, view_fits, or bans_edit....
    """
    __tablename__ = 'permissions'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(150), unique=True)

    roles_needed = relationship("Role", secondary=permission_roles)

    def __repr__(self):
        return f'<Permission id={self.id} name={self.name}'


class Waitlist(Base):
    """
    Represents a waitlist
    """
    __tablename__ = 'waitlists'
    __table_args__ = (
        UniqueConstraint('group_id', 'waitlist_type', name='uq_waitlists_group_id_waitlist_type'),
    )

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(50))
    waitlistType = Column('waitlist_type', String(20))
    groupID = Column('group_id', Integer, ForeignKey("waitlist_groups.group_id"),)
    displayTitle = Column('display_title', String(100), nullable=False, default="")
    entries = relationship("WaitlistEntry", back_populates="waitlist", order_by="asc(WaitlistEntry.creation)")
    group = relationship("WaitlistGroup", back_populates="waitlists")

    def __repr__(self):
        return "<Waitlist %r>" % self.name

class WaitlistGroup(Base):
    """
    Represents a waitlist Group,
    A waitlist group always contains 1 x-up list
    and 3 approved lists for dps, 1 for sniper and 1 for logi
    and can contain an other one for out of line ships
    """

    __tablename__ = "waitlist_groups"

    groupID = Column('group_id', Integer, primary_key=True)
    groupName = Column('group_name', String(50), unique=True, nullable=False)
    displayName = Column('display_name', String(50), unique=True, nullable=False)
    """
    xupwlID = Column('xupwl_id', Integer, ForeignKey(Waitlist.id), nullable=False)
    logiwlID = Column('logiwl_id', Integer, ForeignKey(Waitlist.id), nullable=False)
    dpswlID = Column('dpswl_id', Integer, ForeignKey(Waitlist.id), nullable=False)
    sniperwlID = Column('sniperwl_id', Integer, ForeignKey(Waitlist.id), nullable=False)
    otherwlID = Column('otherwl_id', Integer, ForeignKey(Waitlist.id), nullable=True)
    """
    enabled = Column('enabled', Boolean(name='enabled'), nullable=False, default=False)
    status = Column('status', String(1000), default="Down")
    dockupID = Column('dockup_id', Integer, ForeignKey(Station.stationID), nullable=True)
    systemID = Column('system_id', Integer, ForeignKey(SolarSystem.solarSystemID), nullable=True)
    constellationID = Column('constellation_id', Integer, ForeignKey(Constellation.constellationID), nullable=True)
    ordering = Column('ordering', Integer, nullable=False, default=0)
    influence = Column('influence', Boolean(name='influence'), nullable=False, server_default='0', default=False)

    waitlists = relationship(Waitlist, back_populates="group")

    def has_wl_of_type(self, type: str):
        for wl in self.waitlists:
            if wl.waitlistType == type:
                return True
        return False

    def get_wl_for_type(self, type: str):
        for wl in self.waitlists:
            if wl.waitlistType == type:
                return wl

    def set_wl_to_type(self, wl: Waitlist, type: str):
        if wl is None:
            return
        wl.waitlistType = type
        self.waitlists.append(wl)

    @property
    def xuplist(self):
        return self.get_wl_for_type('xup')
    @xuplist.setter
    def xuplist(self, value: Waitlist):
        self.set_wl_to_type(value, 'xup')

    @property
    def logilist(self):
        return self.get_wl_for_type('logi')
    @logilist.setter
    def logilist(self, value: Waitlist):
        self.set_wl_to_type(value, 'logi')

    @property
    def dpslist(self):
        return self.get_wl_for_type('dps')
    @dpslist.setter
    def dpslist(self, value: Waitlist):
        self.set_wl_to_type(value, 'dps')

    @property
    def sniperlist(self):
        return self.get_wl_for_type('sniper')
    @sniperlist.setter
    def sniperlist(self, value: Waitlist):
        self.set_wl_to_type(value, 'sniper')

    @property
    def otherlist(self):
        return self.get_wl_for_type('other')
    @otherlist.setter
    def otherlist(self, value: Waitlist):
        self.set_wl_to_type(value, 'other')

    #xuplist = relationship("Waitlist", foreign_keys=[xupwlID])
    #logilist = relationship("Waitlist", foreign_keys=[logiwlID])
    #dpslist = relationship("Waitlist", foreign_keys=[dpswlID])
    #sniperlist = relationship("Waitlist", foreign_keys=[sniperwlID])
    #otherlist = relationship("Waitlist", foreign_keys=[otherwlID])


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

    id = Column('id', Integer, primary_key=True)
    ship_type = Column('ship_type', Integer, ForeignKey(InvType.typeID))
    modules = Column('modules', String(5000))
    comment = Column('comment', String(5000))
    wl_type = Column('wl_type', String(10))
    created = Column('created', DateTime, default=datetime.utcnow)

    ship = relationship("InvType")
    waitlist = relationship("WaitlistEntry", secondary="waitlist_entry_fits", uselist=False)

    moduleslist = relationship("FitModule", back_populates="fit")

    def get_dna(self):
        return "{0}:{1}".format(self.ship_type, self.modules)

    def __repr__(self):
        return "<Shipfit id={0} ship_type={1} modules={2} comment={3} waitlist={4}>".format(self.id, self.ship_type,
                                                                                            self.modules, self.comment,
                                                                                            self.waitlist.id)


class WaitlistEntryFit(Base):
    __tablename__ = "waitlist_entry_fits"
    entryID = Column('entry_id', Integer, ForeignKey("waitlist_entries.id", onupdate="CASCADE", ondelete="CASCADE"))
    fitID = Column('fit_id', Integer, ForeignKey("fittings.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)


class WaitlistEntry(Base):
    """
    Represents a person in a waitlist_id
    A person in a waitlist_id always needs to have a user(his character) and and one or more fits
    """
    __tablename__ = "waitlist_entries"
    id = Column('id', Integer, primary_key=True)
    creation = Column('creation', DateTime)
    user = Column('user', Integer, ForeignKey('characters.id'))
    fittings = relationship("Shipfit", secondary="waitlist_entry_fits")
    waitlist_id = Column('waitlist_id', Integer, ForeignKey("waitlists.id", onupdate="CASCADE", ondelete="CASCADE"))
    timeInvited = Column('time_invited', DateTime, default=None)
    inviteCount = Column('invite_count', Integer, default=0)
    waitlist = relationship("Waitlist", back_populates="entries")
    user_data = relationship("Character")

    def __repr__(self):
        return "<WaitlistEntry %r>" % self.id


class APICacheCharacterInfo(Base):
    __tablename__ = "apicache_characterinfo"
    id = Column('id', Integer, primary_key=True)
    characterName = Column('character_name', String(100))
    corporationID = Column('corporation_id', Integer, index=True)
    characterBirthday = Column('character_birthday', DateTime, nullable=False)
    raceID = Column('race_id', Integer)
    expire = Column('expire', DateTime)


class APICacheCorporationInfo(Base):
    __tablename__ = "apicache_corporationinfo"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(100), index=True)
    allianceID = Column('alliance_id', Integer, index=True)
    ceoID = Column('ceo_id', Integer)
    description = Column('description', Text)
    creatorID = Column('creator_id', Integer)
    memberCount = Column('member_count', Integer)
    taxRate = Column('tax_rate', Float)
    ticker = Column('ticker', String(10))
    url = Column('url', String(500))
    creationDate = Column('creation_date', DateTime)
    expire = Column('expire', DateTime)


class APICacheCharacterAffiliation(Base):
    __tablename__ = "apicache_characteraffiliation"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(100), index=True)
    corporationID = Column('corporation_id', Integer, index=True)
    corporationName = Column('corporation_name', String(100), index=True)
    allianceID = Column('alliance_id', Integer, index=True)
    allianceName = Column('alliance_name', String(100), index=True)
    expire = Column('expire', DateTime)


class APICacheAllianceInfo(Base):
    __tablename__ = 'apicache_allianceinfo'
    id = Column('id', Integer, primary_key=True)
    allianceName = Column('alliance_name', String(100), index=True)
    dateFounded = Column('date_founded', DateTime)
    executorCorpID = Column('executor_corp_id', Integer, index=True)
    ticker = Column('ticker', String(10))
    expire = Column('expire', DateTime)


class Ban(Base):
    __tablename__ = "ban"
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(100), index=True)
    reason = Column('reason', Text)
    admin = Column('admin', Integer, ForeignKey("characters.id"))
    admin_obj = relationship("Character", foreign_keys="Ban.admin")


class Whitelist(Base):
    __tablename__ = "whitelist"
    characterID = Column('character_id', Integer, ForeignKey(Character.id), primary_key=True)
    reason = Column('reason', Text)
    adminID = Column('admin_id', Integer, ForeignKey(Character.id))
    character = relationship(Character, foreign_keys=[characterID])
    admin = relationship(Character, foreign_keys=[adminID])


class Feedback(Base):
    """
    Contains the feedback people give about the waitlist
    """
    __tablename__ = "feedback"
    id = Column('id', Integer, primary_key=True)
    last_changed = Column('last_changed', DateTime, index=True)
    user = Column('user', Integer, ForeignKey(Character.id), unique=True, index=True)
    user_data = relationship("Character")
    likes = Column('likes', Boolean(name='likes'))
    comment = Column('comment', Text)


class Ticket(Base):
    """
    Contains a single 'feedback' entry from a linemember, which can have states
    """
    __tablename__ = "tickets"
    id = Column('id', Integer, primary_key=True)
    title = Column('title', String(50))
    time = Column('time', DateTime, default=datetime.utcnow, nullable=False, index=True)
    characterID = Column('character_id', Integer, ForeignKey('characters.id'), index=True)
    message = Column('message', Text)
    state = Column('state', String(20), nullable=False, index=True, default="new")

    character = relationship("Character")


class IncursionLayout(Base):
    __tablename__ = "incursion_layout"
    constellation = Column('constellation', Integer, ForeignKey(Constellation.constellationID), primary_key=True)
    staging = Column('staging', Integer, ForeignKey(SolarSystem.solarSystemID))
    headquarter = Column('headquarter', Integer, ForeignKey(SolarSystem.solarSystemID))
    dockup = Column('dockup', Integer, ForeignKey(Station.stationID))

    obj_constellation = relationship("Constellation", foreign_keys=[constellation])
    obj_staging = relationship("SolarSystem", foreign_keys=[staging])
    obj_headquarter = relationship("SolarSystem", foreign_keys=[headquarter])
    obj_dockup = relationship("Station", foreign_keys=[dockup])


class HistoryFits(Base):
    __tablename__ = "comp_history_fits"
    id = Column('id', Integer, primary_key=True)
    historyID = Column('history_id', Integer, ForeignKey("comp_history.history_id"))
    fitID = Column('fit_id', Integer, ForeignKey(Shipfit.id))


class HistoryEntry(Base):
    __tablename__ = "comp_history"
    historyID = Column('history_id', Integer, primary_key=True)
    sourceID = Column('source_id', Integer, ForeignKey(Account.id), nullable=True)
    targetID = Column('target_id', Integer, ForeignKey(Character.id), nullable=False)
    action = Column('action', String(20))
    time = Column('time', DateTime, default=datetime.utcnow, index=True)
    exref = Column('exref', Integer, nullable=True, default=None)
    fittings = relationship("Shipfit", secondary='comp_history_fits')
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
    inviteExtID = Column('invite_ext_id', Integer, primary_key=True)
    historyID = Column('history_id', Integer, ForeignKey(HistoryEntry.historyID))
    waitlistID = Column('waitlist_id', Integer, ForeignKey(Waitlist.id))
    timeCreated = Column('time_created', DateTime)
    timeInvited = Column('time_invited', DateTime)


class EventHistoryType(Base):
    __tablename__ = "event_history_types"
    typeID = Column('type_id', Integer, primary_key=True)
    typeName = Column('type_name', String(20), unique=True)


class EventHistoryEntry(Base):
    __tablename__ = "event_history_entries"
    historyID = Column('history_id', Integer, primary_key=True)
    time = Column('time', DateTime, default=datetime.utcnow, index=True)
    typeID = Column('type_id', Integer, ForeignKey("event_history_types.type_id"))

    type = relationship(EventHistoryType, uselist=False)


class EventHistoryInfo(Base):
    __tablename__ = "event_history_info"
    infoID = Column('info_id', Integer, primary_key=True)
    historyID = Column('history_id', Integer, ForeignKey(EventHistoryEntry.historyID))
    infoType = Column('info_type', Integer)
    referenceID = Column('reference_id', Integer)


class TeamspeakDatum(Base):
    __tablename__ = "ts_dati"
    teamspeakID = Column('teamspeak_id', Integer, primary_key=True)
    displayName = Column('display_name', String(128))  # this is displayed in menus and such
    host = Column('host', String(128))  # for internal connection
    port = Column('port', Integer)  # for internal connection
    displayHost = Column('display_host', String(128))  # this should be shown to public
    displayPort = Column('display_port', Integer)  # this should be shown to public
    queryName = Column('query_name', String(128))
    queryPassword = Column('query_password', String(128))
    serverID = Column('server_id', Integer)
    channelID = Column('channel_id', Integer)
    clientName = Column('client_name', String(20))
    safetyChannelID = Column('safety_channel_id', Integer)


class Setting(Base):
    __tablename__ = "settings"
    key = Column('key', String(20), primary_key=True)
    value = Column('value', Text)


class AccountNote(Base):
    __tablename__ = "account_notes"
    entryID = Column('entry_id', Integer, primary_key=True)
    accountID = Column('account_id', Integer, ForeignKey(Account.id), nullable=False)
    byAccountID = Column('by_account_id', Integer, ForeignKey(Account.id), nullable=False)
    note = Column('note', Text, nullable=True)
    time = Column('time', DateTime, default=datetime.utcnow, index=True)
    restriction_level = Column('restriction_level', SmallInteger, default=50, nullable=False, server_default=text('50'))

    role_changes = relationship("RoleChangeEntry", back_populates="note", order_by="desc(RoleChangeEntry.added)")
    by = relationship('Account', foreign_keys=[byAccountID])
    account = relationship('Account', foreign_keys=[accountID])


class RoleChangeEntry(Base):
    __tablename__ = "role_changes"
    roleChangeID = Column('role_change_id', Integer, primary_key=True)
    entryID = Column('entry_id', Integer, ForeignKey(AccountNote.entryID, onupdate="CASCADE", ondelete="CASCADE"),
                     nullable=False)
    roleID = Column('role_id', Integer, ForeignKey(Role.id, onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    added = Column('added', Boolean(name='added'), nullable=False)
    note = relationship(AccountNote, back_populates="role_changes")
    role = relationship(Role)


class FitModule(Base):
    __tablename__ = 'fit_module'
    fitID = Column('fit_id', Integer, ForeignKey(Shipfit.id), primary_key=True, nullable=False)
    moduleID = Column('module_id', Integer, ForeignKey(InvType.typeID), primary_key=True, nullable=False)
    amount = Column('amount', Integer, default=1)
    module = relationship(InvType)
    fit = relationship(Shipfit)


class CalendarEventCategory(Base):
    __tablename__: str = 'calendar_category'
    categoryID: Column = Column('category_id', Integer, primary_key=True)
    categoryName: Column = Column('category_name', String(50), index=True)
    fixedTitle: Column = Column('fixed_title', String(200), nullable=True)
    fixedDescription: Column = Column('fixed_description', Text, nullable=True)


class CalendarEvent(Base):
    __tablename__: str = 'calendar_event'
    eventID: Column = Column('event_id', Integer, primary_key=True)
    eventCreatorID: Column = Column('event_creator_id', Integer, ForeignKey('accounts.id', onupdate='CASCADE', ondelete='CASCADE'),
                                    index=True)
    eventTitle: Column = Column('event_title', Text)
    eventDescription: Column = Column('event_description', Text)
    eventCategoryID: Column = Column('event_category_id', Integer,
                                     ForeignKey(CalendarEventCategory.categoryID, onupdate='CASCADE', ondelete='CASCADE'),
                                     index=True)
    eventApproved: Column = Column('event_approved', Boolean(name='event_approved'), index=True)
    eventTime: Column = Column('event_time', DateTime, index=True)
    approverID: Column = Column('approver_id', Integer, ForeignKey('accounts.id', ondelete='CASCADE', onupdate='CASCADE'))

    creator: relationship = relationship(Account, foreign_keys=[eventCreatorID])
    eventCategory: relationship = relationship(CalendarEventCategory)
    organizers: relationship = relationship(Account, secondary="calendar_organizer")
    backseats: relationship = relationship(Account, secondary="calendar_backseat")
    approver: relationship = relationship(Account, foreign_keys=[approverID])


calendar_organizer: Table = Table('calendar_organizer',
                                  Base.metadata,
                                  Column('account_id', Integer,
                                         ForeignKey(Account.id, ondelete="CASCADE", onupdate='CASCADE')),
                                  Column('event_id', Integer,
                                         ForeignKey(CalendarEvent.eventID, ondelete="CASCADE", onupdate='CASCADE'))
                                  )

calendar_backseat: Table = Table('calendar_backseat',
                                 Base.metadata,
                                 Column('account_id', Integer,
                                        ForeignKey(Account.id, ondelete="CASCADE", onupdate='CASCADE')),
                                 Column('event_id', Integer,
                                        ForeignKey(CalendarEvent.eventID, ondelete="CASCADE", onupdate='CASCADE'))
                                 )


class CCVote(Base):
    __tablename__ = "ccvote"
    ccvoteID = Column('ccvote_id', Integer, primary_key=True)
    voterID = Column('voter_id', Integer, ForeignKey(Character.id))
    lmvoteID = Column('lmvote_id', Integer, ForeignKey(Account.id))
    fcvoteID = Column('fcvote_id', Integer, ForeignKey(Account.id))
    time = Column('time', DateTime, default=datetime.utcnow)


class Trivia(Base):
    __tablename__: str = 'trivia'
    __table_args__ = (
        CheckConstraint('to_time > from_time', name="to_bigger_from"),
    )
    triviaID: Column = Column('trivia_id', Integer, primary_key=True)
    createdByID: Column = Column('created_by_id', Integer, ForeignKey(Account.id))
    description: Column = Column('description', String(5000))
    alertText: Column = Column('alert_text', String(1000))
    fromTime: Column = Column('from_time', DateTime)
    toTime: Column = Column('to_time', DateTime)

    createdBy = relationship(Account)
    questions = relationship('TriviaQuestion', back_populates='trivia')


class TriviaQuestion(Base):
    __tablename__: str = 'trivia_question'
    questionID: Column = Column('question_id', Integer, primary_key=True)
    triviaID: Column = Column('trivia_id', Integer, ForeignKey(Trivia.triviaID), nullable=False)
    questionText: Column = Column('question_text', String(1000))
    answerType: Column = Column('answer_type', String(255))
    answerConnection: Column = Column('answer_connection', Enum('AND', 'OR', 'NOT', 'NONE', name="answer_connection"))
    inputPlaceholder: Column = Column('input_placeholder', String(255))

    trivia = relationship(Trivia, back_populates='questions')
    answers = relationship('TriviaAnswer')


class TriviaAnswer(Base):
    __tablename__: str = 'trivia_answer'
    answerID: Column = Column('answer_id', Integer, primary_key=True)
    questionID: Column = Column('question_id', Integer, ForeignKey(TriviaQuestion.questionID), primary_key=True)
    answerText: Column = Column('answer_text', String(1000))


class TriviaSubmission(Base):
    __tablename__: str = 'trivia_submission'
    submissionID: Column = Column('submission_id', Integer, primary_key=True)
    triviaID: Column = Column('trivia_id', Integer, ForeignKey(Trivia.triviaID))
    submittorID: Column = Column('submittor_id', Integer, ForeignKey(Character.id), nullable=True)
    submittorAccountID: Column = Column('submittor_account_id', Integer, ForeignKey(Account.id), nullable=True)

    account = relationship(Account)
    character = relationship(Character)
    answers = relationship('TriviaSubmissionAnswer', back_populates='submission')


class TriviaSubmissionAnswer(Base):
    __tablename__: str = 'trivia_submission_answer'
    submissionID: Column = Column('submission_id', Integer, ForeignKey(TriviaSubmission.submissionID), primary_key=True)
    questionID: Column = Column('question_id', Integer, ForeignKey(TriviaQuestion.questionID), primary_key=True)
    answerText: Column = Column('answer_text', String(5000))

    submission = relationship(TriviaSubmission, back_populates='answers')
    question = relationship(TriviaQuestion)
