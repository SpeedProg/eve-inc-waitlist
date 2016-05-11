from ts3.query import TS3Connection, TS3QueryError
from waitlist.utility.config import ts_host, ts_port, ts_query_name,\
    ts_query_pass, ts_server_id, ts_channel_id, ts_client_name
import logging

logger = logging.getLogger(__name__)

def make_connection():
    con = TS3Connection(ts_host, ts_port)

    try :
        con.login(client_login_name=ts_query_name, client_login_password=ts_query_pass)
        con.use(sid=ts_server_id)
        con.clientupdate(CLIENT_NICKNAME=ts_client_name)
        con.clientmove(0, ts_channel_id)
    except TS3QueryError as ex:
        logger.error("Failed to connect to T3Query %s", ex.resp.error['msg'])
        con = None
    return con

conn = make_connection()

def handle_dc(func, *args, **kwargs):
    def func_wrapper(*args, **kwargs):
        global conn
        if conn is not None:
            try:
                func(*args, **kwargs)
            except:
                    conn = make_connection()
                    func(*args, **kwargs)
        else:
            logger.error("No TS Connection")
    return func_wrapper

@handle_dc
def send_poke(name, msg):
    response = conn.clientfind(pattern=name)
    for resp in response:
        conn.clientpoke(msg, resp['clid'])
    


