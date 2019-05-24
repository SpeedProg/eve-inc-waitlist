import logging
from typing import Set, List, Optional, Any
import grpc
from flask_babel import lazy_gettext

from waitlist.base import db
from waitlist.storage.database import Account, MurmurUser
from waitlist.utility.settings import sget_active_coms_type, sget_active_coms_id
from waitlist.storage.database import MurmurDatum

from . import murmurrpc_pb2
from . import murmurrpc_pb2_grpc

from ..coms import ComConnector

logger = logging.getLogger(__name__)


role_mappings = [('fullcommander', {'fc', 'lm'}),
                ('trainee', {'tbadge', 'resident'}),
                ('officer', {'officer'}),
                ('leadership', {'leadership'}),
                ('fc', {'fc'}),
                ('lm', {'lm'}),
                ('t_fc', {'tbadge'}),
                ('t_lm', {'resident'}),
                ('ct_fc', {'Certified FC Trainer'}),
                ('ct_lm', {'Certified LM Trainer'}),
                ('t_ct_fc', {'Training Certified FC Trainer'}),
                ('t_ct_lm', {'Training Certified LM Trainer'}),
                ('ct', {'Certified FC Trainer', 'Certified LM Trainer', 'Training Certified FC Trainer', 'Training Certified LM Trainer'})
                ]

class MurmurConnector(ComConnector):

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def __get_active_murmur_datum() -> Optional[MurmurDatum]:
        if not (sget_active_coms_type() == 'murmur'):
            return None
        active_id = sget_active_coms_id()
        if active_id is None:
            return None
        return db.session.query(MurmurDatum).get(active_id)

    @staticmethod
    def __get_channel(info: MurmurDatum) -> Any:
        return grpc.insecure_channel(info.grpcHost+':'+str(info.grpcPort))

    def register_user(self, name: str, password: str, acc_id: int) -> None :
        acc: Account = db.session.query(Account).get(acc_id)
        murmur_user: MurmurUser = db.session.query(MurmurUser).filter(MurmurUser.accountID == acc_id).first()
        with grpc.insecure_channel('localhost:50051') as ch:
            client = murmurrpc_pb2_grpc.V1Stub(ch)
            server = murmurrpc_pb2.Server(id=1)
            if murmur_user is not None:
                # lets get the user data and compare
                dbuser = murmurrpc_pb2.DatabaseUser(server=server, id=murmur_user.murmurUserID)
                dbuser = client.DatabaseUserGet(dbuser)
                dbuser.id = murmur_user.murmurUserID
                if dbuser.name != name:
                    # not our user, so remove his stuff
                    client.DatabaseUserDeregister(dbuser)
                    db.session.delete(murmur_user)
                    db.session.commit()
                else:
                    # our user lets just change his pw
                    dbuser.password = password
                    client.DatabaseUserUpdate(dbuser)
                    return

            else:  # we got no connected user yet
                ul = client.DatabaseUserQuery(murmurrpc_pb2.DatabaseUser.Query(server=server, filter=name))
                target_db_user = None
                for u in ul.users:
                    if u.name == name:
                        target_db_user = u
                        break
                if target_db_user is not None:
                    # lets deregister him since we where not connected before
                    user = murmurrpc_pb2.DatabaseUser(server=server, id=target_db_user.id)
                    client.DatabaseUserDeregister(user)

            # register the new user
            user = murmurrpc_pb2.DatabaseUser(server=server, name=name, password=password)
            user = client.DatabaseUserRegister(user)
            murmur_user: MurmurUser = MurmurUser(accountID=acc_id, murmurUserID=user.id)
            db.session.add(murmur_user)
            db.session.commit()

        return 0

    @staticmethod
    def __get_murmur_groups_from_roles(roles: Set[str]) ->  Set[str]:
        out_groups: List[str] = []

        for r in roles:
            for mapping in role_mappings:
                if r in mapping[1]:
                    out_groups.append(mapping[0])
        return set(out_groups)


    def update_user_rights(self, account_id: int) -> None:
        server = murmurrpc_pb2.Server(id=1)
        acc: Account = db.session.query(Account).get(account_id)
        if acc.get_eve_name() == '':
          return
        user_roles: Set[str] = set()
        for role in acc.roles:
            user_roles.add(role.name)

        murmur_grps = MurmurConnector.__get_murmur_groups_from_roles(user_roles)


        with grpc.insecure_channel('localhost:50051') as ch:
            client = murmurrpc_pb2_grpc.V1Stub(ch)

            # lets get the murmur user so we know who to add to groups
            murmur_user = None
            user_list = client.DatabaseUserQuery(murmurrpc_pb2.DatabaseUser.Query(server=server, filter=acc.get_eve_name()))
            for u in user_list.users:
                if u.name == acc.get_eve_name():
                    murmur_user = u
                    break

            if murmur_user is None:
                logger.error('Registration failed no user with name %s found', acc.get_eve_name())
                return

            channel_list = client.ChannelQuery(murmurrpc_pb2.Channel.Query(server=server))
            target_channel = None
            for c in channel_list.channels:
                if c.id == 0:
                    target_channel = c
                    break

            if target_channel is None:
                logger.error('Failed to find channel for adding rights')
                return

            acl_list = client.ACLGet(target_channel)
            acl_list.server.id=server.id
            acl_list.channel.id = target_channel.id


            for group in acl_list.groups:
                if group.name in murmur_grps:
                    is_already_in = False
                    for u in group.users_add:
                        if u.name == murmur_user.name:
                            is_already_in = True
                            break

                    if not is_already_in:
                        n_user = group.users_add.add()
                        n_user.CopyFrom(murmur_user)
                else:  # he should not have this group so we need to remove him if he does
                    for i in range(len(group.users_add)):
                        if group.users_add[i].name == murmur_user.name:
                            del group.users_add[i]
                            break;

            client.ACLSet(acl_list)

    def send_notification(self, username: str, msg: str) -> None:
        murmur_datum: Optional[MurmurDatum] = MurmurConnector.__get_active_murmur_datum()
        if murmur_datum is None:
            return

        with MurmurConnector.__get_channel(murmur_datum) as ch:
            client = murmurrpc_pb2_grpc.V1Stub(ch)
            server = murmurrpc_pb2.Server(id=murmur_datum.serverID)
            user_query = client.UserQuery(murmurrpc_pb2.User.Query(server=server))
            t_user = None
            for u in user_query.users:
                if u.name == username:
                    t_user = u
                    break
            if t_user is None:
                return
            t_user = client.UserGet(t_user)

            tmsg = murmurrpc_pb2.TextMessage()
            tmsg.server.id = murmur_datum.serverID
            user = tmsg.users.add()
            user.id = t_user.id
            user.name = t_user.name
            user.session = t_user.session
            tmsg.text = msg
            client.TextMessageSend(tmsg)

    def move_to_safety(self, usernames: List[str]) -> None:
        murmur_datum: Optional[MurmurDatum] = MurmurConnector.__get_active_murmur_datum()
        if murmur_datum is None:
            return

        with MurmurConnector.__get_channel(murmur_datum) as ch:
            client = murmurrpc_pb2_grpc.V1Stub(ch)
            server = murmurrpc_pb2.Server(id=murmur_datum.serverID)
            t_channel = murmurrpc_pb2.Channel(server=server, id=murmur_datum.safetyChannelID)
            user_query = client.UserQuery(murmurrpc_pb2.User.Quer(server=server))
            for u in user_query.users:
                if u.name in usernames:
                    usr = murmurrpc_pb2.User()
                    usr.CopyFrom(u)
                    usr.channel.CopyFrom(t_channel)
                    client.UserUpdate(usr)

    def data_updated(self) -> None:
        # we don't need to do anything on mumble if the coms data changed
        # since for every action we create a new connection
        return

    def close(self) -> None:
        # we don't need this in mumble since we keep no connections open
        return

    def get_connect_display_info(self) -> str:
        datum: MurmurDatum = MurmurConnector.__get_active_murmur_datum()
        if datum is None:
            return 'Not Available'

        return lazy_gettext('Mumble Your username should match exactly: %(host)s:%(port)d', host=datum.displayHost, port=datum.displayPort)

    def get_basic_connect_info(self) -> str:
        datum: MurmurDatum = MurmurConnector.__get_active_murmur_datum()
        if datum is None:
            return 'Not Available'

        return f'Murmur {datum.displayHost}:{datum.displayPort}'

