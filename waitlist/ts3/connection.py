from ts3.query import TS3ServerConnection, TS3QueryError
import logging

from waitlist.utility import config
from waitlist.utility.settings import sget_active_coms_id, sget_active_coms_type
from waitlist.storage.database import TeamspeakDatum
from waitlist.base import db
from time import sleep
from typing import Optional, List
from flask_babel import lazy_gettext

from ..utility.coms import ComConnector

logger = logging.getLogger(__name__)

class TS3Connector(ComConnector):
    class Decorators(object):
        @staticmethod
        def handle_dc(func, **kwargs):
            if config.disable_teamspeak:
                return

            def func_wrapper(*argsw, **kwargsw):
                  if config.disable_teamspeak:
                      return None
                  if argsw[0].conn is not None:
                      try:
                          func(*argsw, **kwargsw)
                      except TS3QueryError as error:
                          logger.error("TS3 Query Error: %s", str(error))
                      except Exception:
                              ncon = TS3Connector.make_connection()
                              if ncon is None:
                                  sleep(2)
                                  ncon = TS3Connector.make_connection()
                                  if ncon is not None:
                                      conn = ncon
                              else:
                                  argsw[0].conn = ncon
                              func(*argsw, **kwargs)
                  else:
                      argsw[0].conn = TS3Connector.make_connection()

            return func_wrapper


    def __init__(self):
        super().__init__()
        self.conn = TS3Connector.make_connection()

    @staticmethod
    def __get_datum() -> Optional[TeamspeakDatum]:
        if sget_active_coms_type() != 'ts3':
            return None
        teamspeak_id = sget_active_coms_id()
        if teamspeak_id is None:
            return None
        return db.session.query(TeamspeakDatum).get(teamspeak_id)

    @staticmethod
    def make_connection():
        if config.disable_teamspeak:
            return None

        teamspeak = TS3Connector.__get_datum()
        if teamspeak is None:
            return None
        try:
            ts3conn = TS3ServerConnection(f'ssh://{teamspeak.queryName}:{teamspeak.queryPassword}@{teamspeak.host}:{teamspeak.port}')
            ts3conn.exec_("use", sid=teamspeak.serverID)
            try:
                ts3conn.exec_('clientupdate', client_nickname=teamspeak.clientName)
            except TS3QueryError as ex:
                # this means we already have the right name
                # newer versions of ts server name without ip
                pass
            try:
                ts3conn.exec_('clientmove', cid=teamspeak.channelID, clid=0)
            except TS3QueryError as ex:
                if ex.resp.error['msg'] == "already member of channel":
                    pass
                else:
                    logger.error("Failed to connect to T3Query %s", ex.resp.error['msg'])
                    ts3conn = None
        except TS3QueryError as ex:
            logger.error("Failed to connect to T3Query %s", ex.resp.error['msg'])
            ts3conn = None
        except Exception as ex:
            logger.error("Failed to connect to T3Query %s", ex)
            ts3conn = None
        return ts3conn

    def change_connection(self):
        if config.disable_teamspeak:
            return
        if self.conn is not None:
            self.conn.close()
        self.conn = TS3Connector.make_connection()

    @Decorators.handle_dc
    def send_notification(self, name: str, msg: str) -> None:
        if config.disable_teamspeak:
            return
        try:
            response = self.conn.exec_('clientfind', pattern=name)
        except TS3QueryError as er:
            logger.info("TS3 ClientFind failed on %s with %s", name, str(er))
            response = []
        found = False
        for resp in response:
            if resp['client_nickname'] == name:
                self.conn.exec_('clientpoke', clid=resp['clid'], msg=msg)
                found = True
        # deaf people put a * in front
        if not found:
            try:
                response = self.conn.clientfind(pattern="*"+name)
            except TS3QueryError as er:
                logger.info("TS3 ClientFind failed on %s with %s", "*"+name, str(er))
                return
            for resp in response:
                if resp['client_nickname'] == "*"+name:
                    self.conn.exec_('clientpoke', msg=msg, clid=resp['clid'])


    @Decorators.handle_dc
    def move_to_safety(self, names: List[str]) -> None:
        if config.disable_teamspeak:
            return

        if self.conn is None:
            return

        ts_datum: TeamspeakDatum = TS3Connector.__get_datum()

        for name in names:
            try:
                response = self.conn.exec_('clientfind', pattern=name)
            except TS3QueryError as er:
                logger.info("TS3 ClientFind failed on %s with %s", name, str(er))
                response = []
            client = None
            for resp in response:
                if resp['client_nickname'] == name:
                    client = resp
                    break

            if client is None:
                try:
                    response = self.conn.exec_('clientfind', pattern="*"+name)
                except TS3QueryError as er:
                    logger.info("TS3 ClientFind failed on %s with %s", "*"+name, str(er))
                    return
                for resp in response:
                    if resp['client_nickname'] == "*"+name:
                        client = resp
                        break
            if client is None:  # we didn't find a user
                return
            self.conn.exec_('clientmove', clid=client['clid'], cid=ts_datum.safetyChannelID)

    def register_user(self, name: str, password: str, acc_id: int) -> str:
        return name

    def update_user_rights(self, wl_account_id: int, name: str) -> str:
        return name

    def data_updated(self) -> None:
        self.change_connection()

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()

    def get_connect_display_info(self) -> str:
        ts: TeamspeakDatum = TS3Connector.__get_datum()
        if ts is None:
            return 'Not Available'
        return lazy_gettext('TeamSpeak3 Your username should match exactly: %(host)s:%(port)d', host=ts.displayHost, port=ts.displayPort)

    def get_basic_connect_info(self) ->  str:
        ts: TeamspeakDatum = TS3Connector.__get_datum()
        if ts is None:
            return 'Not Available'

        return f'{ts.displayHost}:{ts.displayPort}'
