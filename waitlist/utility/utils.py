import string
import random
import logging
import re

logger = logging.getLogger(__name__)


class LogMixin(object):
    @property
    def logger(self):
        name = '.'.join([__name__, self.__class__.__name__])
        return logging.getLogger(name)


def get_random_token(length):
    return str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length)))


def create_dna_string(mod_map):
    dna = ""
    for mod_id in mod_map:
        mod = mod_map[mod_id]
        dna += str(mod[0]) + ";" + str(mod[1]) + ":"
    if dna == "":  # if there is no module
        return ":"
    return dna+":"  # dna always needs to end with 2 colons


# map looks like this mod_map = {mod_id:[mod_id,mod_count],...}
def create_mod_map(dna_string):
    mod_map = {}
    mods = dna_string.split(':')
    for mod in mods:
        if not mod:
            continue
        parts = mod.split(";")
        mod_id = int(parts[0])
        if len(parts) > 1:
            mod_count = int(parts[1])
            if mod_count > 2147483647 or mod_count < 0:
                raise ValueError("Mod amount is out of range of signed int")
        else:
            raise ValueError("Mod did not contain an amount")
        mod_map[mod_id] = [mod_id, mod_count]
    
    return mod_map


def get_fit_format(line):
    # [Vindicator, VeniVindiVG]
    if re.match("\[.*,.*\]", line):
        return "eft"
    else:  # just consider everyhting else dna
        return "dna"


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
