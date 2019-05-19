import logging
from typing import Set, List
import grpc

from waitlist.base import db
from waitlist.storage.database import Account

from . import murmurrpc_pb2
from . import murmurrpc_pb2_grpc


logger = logging.getLogger(__name__)


def register_user(name: str, password: str) -> int:
    with grpc.insecure_channel('localhost:50051') as ch:
        client = murmurrpc_pb2_grpc.V1Stub(ch)
        server = murmurrpc_pb2.Server(id=1)
        ul = client.DatabaseUserQuery(murmurrpc_pb2.DatabaseUser.Query(server=server, filter=name))
        target_db_user = None
        for u in ul.users:
            if u.name == name:
                target_db_user = u
                break
        if target_db_user is not None:
            logger.error('User with name %s already registered on murmur', name)
            return 1
        user = murmurrpc_pb2.DatabaseUser(server=server, name=name, password=password)
        client.DatabaseUserRegister(user)
        return 0


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
def get_murmur_groups_from_roles(roles: Set[str]) ->  Set[str]:
    out_groups: List[str] = []

    for r in roles:
        for mapping in role_mappings:
            if r in mapping[1]:
                out_groups.append(mapping[0])
    return set(out_groups)


def setup_user_rights(account_id: int) -> None:
    server = murmurrpc_pb2.Server(id=1)
    acc: Account = db.session.query(Account).get(account_id)
    if acc.get_eve_name() == '':
      return
    user_roles: Set[str] = set()
    for role in acc.roles:
        user_roles.add(role.name)

    murmur_grps = get_murmur_groups_from_roles(user_roles)


    with grpc.insecure_channel('localhost:50051') as ch:
        client = murmurrpc_pb2_grpc.V1Stub(ch)

        # lets get the murmur user so we know who to add to groups
        murmur_user = None
        user_list = client.DatabaseUserQuery(murmurrpc_pb2.DatabaseUser.Query(server=server, filter=acc.get_eve_name()))
        for u in user_list.users:
            if u.name == acc.current_char_obj.eve_name:
                murmur_user = u
                break

        if murmur_user is None:
            logger.error('Registration failed no user with name %s found', acc.current_char_obj.eve_name)
            return

        channel_list = client.ChannelQuery(murmurrpc_pb2.Channel.Query(server=server))
        target_channel = None
        for c in channel_list.channels:
            if c.name == 'Root':
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

        client.ACLSet(acl_list)


