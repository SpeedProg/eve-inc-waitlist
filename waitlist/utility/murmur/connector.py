import logging
import re
from typing import Set, List, Optional, Any
import grpc
from flask_babel import lazy_gettext

from waitlist.base import db
from waitlist.storage.database import Account, MurmurUser, Role
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

class Tag(object):
    def __init__(self, code: str, sort: int) -> None:
        self.code = code
        self.sort = sort

    def __eq__(self, other):
        return self.code.__eq__(other)

    def __ne__(self, other):
        return self.code.__ne__(other)

    def __hash__(self):
        return self.code.__hash__()


badge_mapping = {
    'leadership': {Tag('L', 0)},
    'officer': {Tag('O', 1)},
    'fc': {Tag('FC', 4)},
    'lm': {Tag('LM', 5)},
    'Certified FC Trainer': {Tag('CF', 2)},
    'Certified LM Trainer': {Tag('CL', 3)},
    'tbadge': {Tag('T', 6)},
    'resident': {Tag('R', 7)}
}

badge_fusions = {
    Tag('M', 2): {Tag('CF', 0), Tag('CL', 0)}
}


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

    @staticmethod
    def __get_badges_for_account(acc: Account) -> Set[str]:
        badge_set = set()
        for role in acc.roles:
            if role.name in badge_mapping:
                badge_set.update(badge_mapping[role.name])
        # now that we have all basic ones, fuse badges that equal an other one
        # while it is changing reapply fusions
        changed = True
        while changed:
            new_set = badge_set.copy()
            for fusion_result in badge_fusions:
                if badge_fusions[fusion_result] <= new_set:
                    # if the required ones are a subset, then replace them
                    new_set -= badge_fusions[fusion_result]
                    new_set.add(fusion_result)

            if new_set == badge_set:
                changed = False
            badge_set = new_set

        return badge_set

    @staticmethod
    def __get_username_with_badged(username: str, badges: Set[str]) -> str:
        badge_list = list(badges)
        badge_list.sort(key=lambda x: x.sort)
        badge_str = ''
        if len(badge_list) > 0:
            badge_str = '['+(']['.join([t.code for t in badge_list]))+']'
        print('Username:', badge_str + username)
        return badge_str + username

    @staticmethod
    def __get_final_username(username: str, acc: Account) -> str:
        badges = MurmurConnector.__get_badges_for_account(acc)
        return MurmurConnector.__get_username_with_badged(username, badges)

    def register_user(self, name: str, password: str, acc_id: int) -> str :
        acc: Account = db.session.query(Account).get(acc_id)
        final_name = MurmurConnector.__get_final_username(name, acc)
        with grpc.insecure_channel('localhost:50051') as ch:
            client = murmurrpc_pb2_grpc.V1Stub(ch)
            server = murmurrpc_pb2.Server(id=1)
            murmur_user: MurmurUser = db.session.query(MurmurUser).filter(MurmurUser.accountID == acc_id).first()
            if murmur_user is not None:
                # lets get the user data and compare
                dbuser = murmurrpc_pb2.DatabaseUser(server=server, id=murmur_user.murmurUserID)
                try:
                    dbuser = client.DatabaseUserGet(dbuser)
                    dbuser.id = murmur_user.murmurUserID
                    if dbuser.name != final_name:
                        # not our user, so remove his stuff
                        client.DatabaseUserDeregister(dbuser)
                        db.session.delete(murmur_user)
                        db.session.commit()
                    else:
                        # our user lets just change his pw
                        dbuser.password = password
                        client.DatabaseUserUpdate(dbuser)
                        return final_name
                except grpc.RpcError as err:
                    if err.details() == "invalid user":
                        db.session.delete(murmur_user)
                        db.session.commit()
                    else:  # raise it further because it is unexpected
                        raise err

            else:  # we got no connected user yet
                # lets find everything that ends with the basename
                ul = client.DatabaseUserQuery(murmurrpc_pb2.DatabaseUser.Query(server=server, filter='%'+name))
                target_db_user_list = []
                # now we need to go through all found users and make sure
                # none of them matches (\[[A-Z]+\])*username
                char_name_re = '(?:\[[A-Z]+\])*'+ re.escape(name)
                char_name_cre = re.compile(char_name_re)
                for u in ul.users:
                    if char_name_cre.fullmatch(u.name):
                        target_db_user_list.append(u)

                # deregister all the found users, since we are not bound to them
                for user in target_db_user_list:
                    user = murmurrpc_pb2.DatabaseUser(server=server, id=user.id)
                    client.DatabaseUserDeregister(user)

            # register the new user
            user = murmurrpc_pb2.DatabaseUser(server=server, name=final_name, password=password)
            user = client.DatabaseUserRegister(user)
            murmur_user: MurmurUser = MurmurUser(accountID=acc_id, murmurUserID=user.id)
            db.session.add(murmur_user)
            db.session.commit()

        return final_name

    @staticmethod
    def __get_murmur_groups_from_roles(roles: Set[str]) ->  Set[str]:
        out_groups: List[str] = []

        for r in roles:
            for mapping in role_mappings:
                if r in mapping[1]:
                    out_groups.append(mapping[0])
        return set(out_groups)


    def update_user_rights(self, account_id: int, name: str) -> None:
        server = murmurrpc_pb2.Server(id=1)
        acc: Account = db.session.query(Account).get(account_id)
        db_murmur_user: MurmurUser = db.session.query(MurmurUser).filter(MurmurUser.accountID == account_id).first()
        if db_murmur_user is None:
            return 'Not registered'

        final_name = MurmurConnector.__get_final_username(name, acc)

        if name == '':
          return
        user_roles: Set[str] = set()
        for role in acc.roles:
            user_roles.add(role.name)

        murmur_grps = MurmurConnector.__get_murmur_groups_from_roles(user_roles)

        with grpc.insecure_channel('localhost:50051') as ch:
            client = murmurrpc_pb2_grpc.V1Stub(ch)

            # lets get the murmur user so we know who to add to groups
            murmur_user = None
            try:
                murmur_user = client.DatabaseUserGet(murmurrpc_pb2.DatabaseUser(id=db_murmur_user.murmurUserID))
            except grpc.RpcError as err:
                if err.details() == 'invalid user':
                    logger.info('Registration failed no user with id %d found', db_murmur_user.murmurUserID)
                    db.session.delete(db_murmur_user)
                    db.session.commit()
                else:
                    logger.error('Unknown error when trying to get user as in database %s', err.details())
                return 'Unknown'

            if acc.disabled:
                # if the acc is disabled he should not be registered anymore!
                # and also be deleted from the waitlist database
                client.DatabaseUserDeregister(murmurrpc_pb2.DatabaseUser(server=server, id=db_murmur_user.murmurUserID))
                db.session.delete(db_murmur_user)
                db.session.commit()
                return 'Account disabled'

            # lets see if we need to update the name, because it might have changed with changed rights
            if murmur_user.name != final_name:
                client.DatabaseUserUpdate(murmurrpc_pb2.DatabaseUser(server=server, id=murmur_user.id, name=final_name))
                murmur_user.name = final_name

            channel_list = client.ChannelQuery(murmurrpc_pb2.Channel.Query(server=server))
            target_channel = None
            for c in channel_list.channels:
                if c.id == 0: # root channel has ID 0
                    target_channel = c
                    break

            if target_channel is None:
                logger.error('Failed to find channel for adding rights')
                return final_name

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
        return final_name

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

