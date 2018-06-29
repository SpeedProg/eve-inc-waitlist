import logging
from datetime import datetime, timedelta
from typing import List, Optional, Union, Dict, Any

from esipy import EsiSecurity
from esipy.exceptions import APIException
from sqlalchemy import Column, Integer, String, SmallInteger, BIGINT, Boolean, DateTime, Index, \
    sql, BigInteger, text, Float, Text
from sqlalchemy import Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Table, ForeignKey, CheckConstraint, UniqueConstraint

from waitlist import db
from waitlist.utility import config
from waitlist.utility.utils import get_random_token
from sqlalchemy.types import UnicodeText
import json
import inspect
import traceback

logger = logging.getLogger(__name__)

Base = db.Model

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
    tokenID = Column('token_id', Integer, ForeignKey('ssotoken.token_id', onupdate="CASCADE", ondelete="CASCADE"),
                     primary_key=True)
    scopeName = Column('scope_name', String(100), nullable=False, primary_key=True, default='')


class SSOToken(Base):
    __tablename__ = 'ssotoken'
    __table_args__ = (Index('ix_character_id_account_id', 'character_id', 'account_id'), )
    tokenID = Column('token_id', Integer, primary_key=True)
    characterID = Column('character_id', Integer, ForeignKey('characters.id', onupdate="CASCADE", ondelete="CASCADE"),
                         nullable=False,
                         index=True)
    # the last account that used this char, if null means no account=>standalone char
    accountID = Column('account_id', Integer, ForeignKey('accounts.id', onupdate="CASCADE", ondelete="CASCADE"),
                       nullable=True, index=True)
    refresh_token = Column('refresh_token', String(128), default=None)
    access_token = Column('access_token', String(128), default=None)
    access_token_expires = Column('access_token_expires', DateTime, default=datetime.utcnow)

    scopes: List[EveApiScope] = relationship(EveApiScope, cascade="save-update, merge, delete, delete-orphan")

    def has_scopes(self, scopes: List[str]):
        for searched_scope in scopes:
            scope_found = False
            for token_scope in self.scopes:
                if searched_scope == token_scope.scopeName:
                    scope_found = True
                    break
            if not scope_found:
                return False

        return True

    @staticmethod
    def update_token_callback(token_identifier: int, access_token: str, refresh_token: str, expires_at: int,
                              **_: Dict[str, Any]) -> None:
        logger.debug("Updating token with id=%s", token_identifier)
        token: SSOToken = db.session.query(SSOToken).get(token_identifier)
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.access_token_expires = datetime.utcfromtimestamp(expires_at)
        db.session.commit()

    @property
    def is_valid(self) -> bool:
        """
        Checks if this token still works
        Also updates it's own tokens data if it works
        :return: True if the token is still valid otherwise False
        """

        # if the access_token is still not expired return as valid
        if self.access_token_expires > datetime.utcnow()+timedelta(seconds=10):
            logger.debug("%s valid because access_token_expires %s still more then 10s in the future",
                         self, self.access_token_expires)
            return True

        # check that the token is valid
        security: EsiSecurity = EsiSecurity('', config.crest_client_id,
                                            config.crest_client_secret,
                                            headers={
                                                'User-Agent': config.user_agent
                                            })
        security.update_token(self.info_for_esi_security())

        try:
            frame = inspect.currentframe()
            stack_trace = traceback.format_stack(frame)
            logger.debug("Calling refresh on %r", self)
            logger.debug(stack_trace[:-1])
            security.refresh()
            SSOToken.update_token_callback(token_identifier=self.tokenID, access_token=security.access_token,
                                           refresh_token=security.refresh_token, expires_at=security.token_expiry)
            logger.debug("Token refresh worked")
            return True
        except APIException as e:
            # this probably happens because the token is invalid now
            if ('message' in e.response and
                    (e.response['message'] == 'invalid_token' or
                     e.response['message'] == 'invalid_request')
                )\
                or\
                ('error' in e.response and
                      (e.response['error'] == 'invalid_request' or
                       e.response['error'] == 'invalid_token')
            ):
                logger.debug("%s invalid because of response %s.", self, e.response)
                return False

            logger.exception(e)
            if hasattr(e, 'text'):
                logger.error("%s valid because of exception. text = %s", self, e.text)
            return True

    def expires_in(self) -> int:
        """ Get amount of seconds until expiry.

        :return: how many seconds the access_token is still valid for
        """
        return int((self.access_token_expires - datetime.utcnow()).total_seconds())

    def info_for_esi_security(self) -> Dict[str, Union[str, int]]:
        """
        Information formatted to passing to EsiSecurity.update_token

        :return: a dict containing token info
        """
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.expires_in()
        }

    def update_token_data(self, access_token: Optional[str] = None, refresh_token: Optional[str] = None,
                          expires_at: Optional[datetime] = None, scopes: Optional[str] = None) -> None:
        if access_token is not None:
            self.access_token = access_token

        if refresh_token is not None:
            self.refresh_token = refresh_token

        if expires_at is not None:
            self.access_token_expires = expires_at

        if scopes is not None:
            scope_name_list: List[str] = scopes.split(" ")
            token_scopes: List[EveApiScope] = []

            for scope_name in scope_name_list:
                if scope_name == '':
                    continue
                token_scopes.append(EveApiScope(scopeName=scope_name))

            self.scopes = token_scopes

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'<Token tokenID={self.tokenID} characterID={self.characterID} accountID={self.accountID} refresh_token={self.refresh_token}>'


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
    had_welcome_mail = Column('had_welcome_mail', Boolean(name='had_welcome_mail'),
                              default=False, server_default=sql.expression.false())
    language = Column('language', String(10))

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
        if self.current_char_obj is None:
            return 0
        return self.current_char_obj.lc_level

    @lc_level.setter
    def lc_level(self, val):
        if self.current_char_obj is None:
            return
        self.current_char_obj.lc_level = val

    @property
    def cbs_level(self):
        if self.current_char_obj is None:
            return 0
        return self.current_char_obj.cbs_level

    @cbs_level.setter
    def cbs_level(self, val):
        if self.current_char_obj is None:
            return
        self.current_char_obj.cbs_level = val

    def get_eve_name(self):
        if self.current_char_obj is None:
            return ""
        return self.current_char_obj.eve_name

    def get_eve_id(self):
        return self.current_char

    @property
    def is_new(self):
        if self.current_char_obj is None:
            return False
        return self.current_char_obj.is_new

    @is_new.setter
    def is_new(self, value: bool):
        if self.current_char_obj is None:
            return
        self.current_char_obj.is_new = value

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
        if self.current_char_obj is None:
            return False
        return self.current_char_obj.poke_me

    @poke_me.setter
    def poke_me(self, value: bool):
        if self.current_char_obj is None:
            return
        self.current_char_obj.poke_me = value

    def get_a_sso_token_with_scopes(self, scopes: List[str], character_id: int = None) -> Optional[SSOToken]:
        """
        Gets a token for this account and the given character or current_char that has the given scopes
        and is still valid.
        :param scopes: the scopes the token should have
        :param character_id: id of the character the token should be for or if None uses current_char
        :return: a token that has these scopes or None
        """
        tokens: List[SSOToken] = self.get_sso_tokens_with_scopes(scopes, character_id)
        if len(tokens) <= 0:
            logger.debug("No token found for %s with character %s and scopes %s", self, character_id, scopes)
            return None

        return tokens[0]

    def get_sso_tokens_with_scopes(self, scopes: List[str], character_id: int = None) -> List[SSOToken]:
        """
        Returns a list of tokens for the account and current_char that have the given scopes
        and are still valid.
        :param scopes: the scopes the token needs to have
        :param character_id: id of the character the token should be for or if None uses current_char
        :return: a list of tokens that have the given scopes
        """
        if character_id is None:
            character_id = self.current_char

        if character_id is None:
            return []

        tokens: List[SSOToken] = SSOToken.query\
            .filter((SSOToken.characterID == character_id) & (SSOToken.accountID == self.id)).all()
        logger.debug("Found %s tokens for Account.id=%s and Character.id=%s", len(tokens), self.id, character_id)
        qualified_tokens: List[SSOToken] = []
        for token in tokens:
            if token.has_scopes(scopes):
                logger.debug("Token %s has scopes %s", token.tokenID, scopes)
                if token.is_valid:
                    logger.debug("Token %s is valid", token.tokenID)
                    qualified_tokens.append(token)
                else:
                    logger.debug("Token %s is not valid", token.tokenID)
                    db.session.delete(token)
            else:
                logger.debug("Token %s does not have scopes %s", token.tokenID, scopes)

        db.session.commit()
        return qualified_tokens

    def add_sso_token(self, token: SSOToken):
        if token.characterID is None:
            token.characterID = self.current_char

        if token.accountID is None:
            token.accountID = self.id

        logger.debug("%s adding %s", self, token)
        self.ssoTokens.append(token)

    def get_token_for_charid(self, character_id: int) -> Optional[SSOToken]:
        for token in self.ssoTokens:
            if token.characterID == character_id:
                return token

        return None

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

    def __eq__(self, other) -> int:
        if other is None:
            return False
        if not hasattr(other, 'id'):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return self.id


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
    teamspeak_poke = Column('teamspeak_poke', Boolean(name='teamspeak_poke'),
                            default=True, server_default="1", nullable=False)
    owner_hash = Column('owner_hash', Text)
    language = Column('language', String(10))

    # this contains all SSOToken for this character
    # normally we only want the ones not associated with an account! we got a property for this
    ssoTokens: List[SSOToken] = relationship('SSOToken')

    accounts = relationship(
        "Account",
        secondary=linked_chars,
        back_populates="characters")

    def get_a_sso_token_with_scopes(self, scopes: List[str]) -> Optional[SSOToken]:
        """
        Gets a token for this Character that has the given scopes
        and is still valid.
        :param scopes: the scopes the token should have
        :return: a token that has these scopes or None
        """
        tokens: List[SSOToken] = self.get_sso_tokens_with_scopes(scopes)
        if len(tokens) <= 0:
            return None

        return tokens[0]

    def get_sso_tokens_with_scopes(self, scopes: List[str]) -> List[SSOToken]:
        """
        Returns a list of tokens for this Character that have the given scopes
        and are still valid.
        :param scopes: the scopes the token needs to have
        :return: a list of tokens that have the given scopes
        """

        # noinspection PyPep8,PyComparisonWithNone
        tokens: List[SSOToken] = SSOToken.query\
            .filter((SSOToken.characterID == self.id) & (SSOToken.accountID == None)).all()
        qualified_tokens: List[SSOToken] = []
        for token in tokens:
            if token.has_scopes(scopes):
                if token.is_valid:
                    qualified_tokens.append(token)
                else:
                    db.session.delete(token)

        db.session.commit()
        return qualified_tokens

    def add_sso_token(self, token: SSOToken):
        if token.characterID is None or token.characterID != self.id:
            token.characterID = self.id

        if token.accountID is not None:
            token.accountID = None
        logger.debug("%s adding %s", self, token)
        self.ssoTokens.append(token)

    def get_login_token(self):
        if self.login_token is None:
            self.login_token = get_random_token(16)
        return self.login_token

    def get_eve_name(self):
        return self.eve_name

    def get_eve_id(self):
        return self.id

    @property
    def is_new(self):
        return self.newbro

    @is_new.setter
    def is_new(self, value: bool) -> None:
        self.newbro = value

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

    def __eq__(self, other) -> int:
        if other is None:
            return False
        if not hasattr(other, 'id'):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return self.id


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

    def has_wl_of_type(self, wl_type: str):
        for wl in self.waitlists:
            if wl.waitlistType == wl_type:
                return True
        return False

    def get_wl_for_type(self, wl_type: str):
        for wl in self.waitlists:
            if wl.waitlistType == wl_type:
                return wl

    def set_wl_to_type(self, wl: Waitlist, wl_type: str):
        if wl is None:
            return
        wl.waitlistType = wl_type
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
    fitID = Column('fit_id', Integer, ForeignKey("fittings.id", onupdate="CASCADE", ondelete="CASCADE"),
                   primary_key=True)


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
    accountID = Column('account_id', Integer, ForeignKey(Account.id),
                       nullable=False)
    byAccountID = Column('by_account_id', Integer, ForeignKey(Account.id),
                         nullable=False)
    note = Column('note', Text, nullable=True, default=None)
    time = Column('time', DateTime, default=datetime.utcnow, index=True)
    restriction_level = Column('restriction_level', SmallInteger, default=50,
                               nullable=False, server_default=text('50'))
    textPayload = Column('text_payload', UnicodeText, nullable=True)
    type = Column('type', String(length=50), nullable=False, index=True)

    role_changes = relationship("RoleChangeEntry", back_populates="note",
                                order_by="desc(RoleChangeEntry.added)")
    by = relationship('Account', foreign_keys=[byAccountID])
    account = relationship('Account', foreign_keys=[accountID])

    @property
    def jsonPayload(self) -> Any:
        if not hasattr(self, '_AccountNote__payload'):
            if self.textPayload is None or self.textPayload == '':
                setattr(self, '_AccountNote__payload', None)
            else:
                setattr(self, '_AccountNote__payload', json.loads(self.textPayload))

        return self.__payload

    @jsonPayload.setter
    def jsonPayload(self, value) -> None:
        if value == '':
            value = None
        self.__payload = value
        self.textPayload = json.dumps(value)

    def __repr__(self):
        return (f'<AccountNote entryID={self.entryID}'
                f' accountID={self.accountID}'
                f' byAccountID={self.byAccountID}'
                f' type={self.type} time={self.time}'
                f' restriction_level={self.restriction_level}'
                f' textPayload={self.textPayload}'
                f' note={self.note}>')


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
    eventCreatorID: Column = Column('event_creator_id', Integer, ForeignKey('accounts.id', onupdate='CASCADE',
                                                                            ondelete='CASCADE'),
                                    index=True)
    eventTitle: Column = Column('event_title', Text)
    eventDescription: Column = Column('event_description', Text)
    eventCategoryID: Column = Column('event_category_id', Integer,
                                     ForeignKey(CalendarEventCategory.categoryID, onupdate='CASCADE',
                                                ondelete='CASCADE'),
                                     index=True)
    eventApproved: Column = Column('event_approved', Boolean(name='event_approved'), index=True)
    eventTime: Column = Column('event_time', DateTime, index=True)
    approverID: Column = Column('approver_id', Integer,
                                ForeignKey('accounts.id', ondelete='CASCADE', onupdate='CASCADE'))

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
