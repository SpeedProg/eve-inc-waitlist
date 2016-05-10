from ts3.query import TS3Connection, TS3QueryError
from waitlist.utility.config import ts_host, ts_port, ts_query_name,\
    ts_query_pass, ts_server_id, ts_channel_id, ts_client_name
import logging

logger = logging.getLogger(__name__)

ts3conn = TS3Connection(ts_host, ts_port)

try :
    ts3conn.login(client_login_name=ts_query_name, client_login_password=ts_query_pass)
    ts3conn.use(sid=ts_server_id)
    ts3conn.clientupdate(CLIENT_NICKNAME=ts_client_name)
    ts3conn.clientmove(0, ts_channel_id)
except TS3QueryError as ex:
    logger.error("Failed to connect to T3Query %s", ex.resp.error['msg'])
    ts3conn = None

def send_poke(name, msg):
    if ts3conn is not None:
        response = ts3conn.clientfind(pattern=name)
        for resp in response:
            ts3conn.clientpoke(msg, resp['clid'])
    else:
        logger.error("No TS Connection")

