import string
import random
import logging

logger = logging.getLogger(__name__)


class LogMixin(object):
    @property
    def logger(self):
        name = '.'.join([__name__, self.__class__.__name__])
        return logging.getLogger(name)


def get_random_token(length):
    return str(''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(length)))


def get_character(user):
    if user.type == "account":
        return user.current_char_obj
    else:
        return user


def get_info_from_ban(ban_line):
    pos_name_end = ban_line.find(" - Reason:\"")
    if pos_name_end != -1:
        reason_end = ban_line.find("\" Admin:\"")
        char_name = ban_line[:pos_name_end]
        reason = ban_line[pos_name_end+11:reason_end]
        admin = ban_line[reason_end+9:-1]
    else:
        char_name = ban_line
        reason = None
        admin = None
    return char_name, reason, admin


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]
