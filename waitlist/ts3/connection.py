from ts3.query import TS3Connection, TS3QueryError
import logging
from waitlist.utility.settings.settings import sget_active_ts_id
from waitlist.storage.database import TeamspeakDatum
from waitlist.base import db
from time import sleep

logger = logging.getLogger(__name__)

def make_connection():
    teamspeakID = sget_active_ts_id()
    if teamspeakID is None:
        return None
    
    teamspeak = db.session.query(TeamspeakDatum).get(teamspeakID)
    try :
        con = TS3Connection(teamspeak.host, teamspeak.port)
        con.login(client_login_name=teamspeak.queryName, client_login_password=teamspeak.queryPassword)
        con.use(sid=teamspeak.serverID)
        con.clientupdate(CLIENT_NICKNAME=teamspeak.clientName)
        con.clientmove(0, teamspeak.channelID)
    except TS3QueryError as ex:
        logger.error("Failed to connect to T3Query %s", ex.resp.error['msg'])
        con = None
    except Exception as ex:
        logger.error("Failed to connect to T3Query %s", ex)
        con = None
    return con

conn = make_connection()

def change_connection():
    global conn
    if conn is not None:
        conn.quit()
    conn = make_connection()

def handle_dc(func, *args, **kwargs):
    def func_wrapper(*args, **kwargs):
        global conn
        if conn is not None:
            try:
                func(*args, **kwargs)
            except TS3QueryError as error:
                logger.error("TS3 Query Error: %", str(error))
            except Exception as ex:
                    logger.error("To call ts %s", ex)
                    ncon = make_connection()
                    if ncon is None:
                        sleep(2)
                        ncon = make_connection()
                        if ncon is not None:
                            conn = ncon
                    else:
                        conn = ncon
                    func(*args, **kwargs)
        else:
            conn = make_connection()
            logger.error("No TS Connection")
    return func_wrapper

@handle_dc
def send_poke(name, msg):
    global conn
    try:
        response = conn.clientfind(pattern=name)
    except TS3QueryError as er:
        logger.info("TS3 ClientFind failed on %s with %s", name, str(er))
        response = []
    found = False
    for resp in response:
        if resp['client_nickname'] == name:
            conn.clientpoke(msg, resp['clid'])
            found = True
    # deaf people put a * in front
    if not found:
        try:
            response = conn.clientfind(pattern="*"+name)
        except TS3QueryError as er:
            logger.info("TS3 ClientFind failed on %s with %s", "*"+name, str(er))
            return
        for resp in response:
            if resp['client_nickname'] == "*"+name:
                conn.clientpoke(msg, resp['clid'])

