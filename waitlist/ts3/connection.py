from ts3.query import TS3ServerConnection, TS3QueryError
import logging

from waitlist.utility import config
from waitlist.utility.settings import sget_active_ts_id
from waitlist.storage.database import TeamspeakDatum
from waitlist.base import db
from time import sleep
from threading import Timer

logger = logging.getLogger(__name__)


def make_connection() -> TS3ServerConnection:
    if config.disable_teamspeak:
        return None

    teamspeak_id = sget_active_ts_id()
    if teamspeak_id is None:
        return None

    teamspeak = db.session.query(TeamspeakDatum).get(teamspeak_id)
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
                logger.error(ex)
                ts3conn = None
    except TS3QueryError as ex:
        logger.error(ex)
        ts3conn = None
    except Exception as ex:
        logger.error("Failed to connect to T3Query %s", ex)
        ts3conn = None
    return ts3conn

def keep_alive():
    global conn
    if conn is not None:
        try:
            conn.send_keepalive()
        except Exception:
            pass
        finally:
            global keepAliveTimer
            keepAliveTimer = Timer(300, keep_alive)

conn: TS3ServerConnection = make_connection()
if conn is not None:
    keepAliveTimer: Timer = Timer(300, keep_alive)
else:
    keepAliveTimer = None

def change_connection():
    if config.disable_teamspeak:
        return
    global conn
    if conn is not None:
        conn.quit()
    conn = make_connection()
    global keepAliveTimer
    if keepAliveTimer is None:
        keepAliveTimer = Timer(300, keep_alive)


def handle_dc(func, **kwargs):
    if config.disable_teamspeak:
        return

    def func_wrapper(*argsw, **kwargsw):
        global conn
        global keepAliveTimer
        if conn is not None:
            try:
                func(*argsw, **kwargsw)
            except TS3QueryError as error:
                logger.error("TS3 Query Error: %s", str(error))
            except Exception:
                    ncon = make_connection()
                    if ncon is None:
                        sleep(2)
                        ncon = make_connection()
                        if ncon is not None:
                            conn = ncon
                            if keepAliveTimer is None:
                                keepAliveTimer = Timer(300, keep_alive)
                    else:
                        conn = ncon
                        if keepAliveTimer is None:
                            keepAliveTimer = Timer(300, keep_alive)
                    func(*argsw, **kwargs)
        else:
            conn = make_connection()
            if keepAliveTimer is None:
                keepAliveTimer = Timer(300, keep_alive)

    return func_wrapper


@handle_dc
def send_poke(name, msg):
    if config.disable_teamspeak:
        return
    global conn

    try:
        response = conn.query('clientfind', pattern=name).all()
    except TS3QueryError as er:
        logger.info("TS3 ClientFind failed on %s with %s", name, str(er))
        response = []
    found = False
    for resp in response:
        if resp['client_nickname'] == name:
            conn.exec_('clientpoke', clid=resp['clid'], msg=msg)
            found = True
    # deaf people put a * in front
    if not found:
        try:
            response = conn.query('clientfind', pattern='*'+name).all()
        except TS3QueryError as er:
            logger.info("TS3 ClientFind failed on %s with %s", "*"+name, str(er))
            return
        for resp in response:
            if resp['client_nickname'] == "*"+name:
                conn.exec_('clientpoke', clid=resp['clid'], msg=msg)


def move_to_safety_channel(name: str, channel_id: int) -> None:
    if config.disable_teamspeak:
        return
    try:
        response = conn.query('clientfind', pattern=name).all()
    except TS3QueryError as er:
        logger.info("TS3 ClientFind failed on %s with %s", name, str(er))
        response = []
    client = None
    for resp in response:
        if resp['client_nickname'] == name:
            client = resp
    
    if client is None:
        try:
            response = conn.query('clientfind', pattern='*'+name).all()
        except TS3QueryError as er:
            logger.info("TS3 ClientFind failed on %s with %s", "*"+name, str(er))
            return
        for resp in response:
            if resp['client_nickname'] == "*"+name:
                client = resp
    if client is None:  # we didn't find a user
        return
    conn.exec_('clientmove', clid=client['clid'], cid=channel_id)
    return
