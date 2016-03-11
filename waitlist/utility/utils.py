import string,random
import logging
import re
from waitlist.storage.database import InvType, Character, Shipfit, Account, Ban
from flask_login import login_required, current_user
from flask.globals import request
from waitlist.data.eve_xml_api import get_character_id_from_name,\
    get_affiliation
from waitlist import db

logger = logging.getLogger(__name__)

class LogMixin(object):
    @property
    def logger(self):
        name = '.'.join([__name__, self.__class__.__name__])
        return logging.getLogger(name)

def get_random_token(length):
    return unicode(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length)))

def parseEft(lines):
        fit = Shipfit()
        # take [Vindicator, VeniVindiVG] remove the [] and split at ,
        info = lines[0][1:-1].split(",", 1)

        ship_type = info[0]  # I only care about what ship it is

        ship_id = get_item_id(ship_type)
        fit.ship_type = ship_id

        mod_map = {}
        for i in range(1, len(lines)):
            mod_name = None
            mod_amount = None

            line = lines[i].strip()
            if not line:
                continue
            
            # check if it is an empty slot
            if re.match("\[[\w\s]+\]$", line):
                continue
            
            # check if it contains a xNUMBER and is by that drone or cargo
            is_cargo = re.match(".*x\d+$", line) is not None
            logger.debug("% is_cargo = %b", line, is_cargo)

            # TODO do we want to enable parsing of EFT/Pyfa fits ?
            # if so we need to filter lines that separate charges by ", "
            if not is_cargo:
                if line.endswith("/OFFLINE"):
                    line = line[:-8]
                name_parts = line.split(", ")
                mod_name = name_parts[0]
                mod_amount = 1
            else:
                mod_info = line.rsplit(" x", 2)
                mod_name = mod_info[0]
                mod_amount = int(mod_info[1])
            
            mod_id = get_item_id(mod_name)
            if mod_id == -1: # items was not in database
                    continue
            
            if mod_id in mod_map:
                mod_entry = mod_map[mod_id]
            else: # if the module is not in the map create it
                
                mod_entry = [mod_id, 0]
                mod_map[mod_id] = mod_entry
            
            mod_entry[1] += mod_amount
        
        fit.modules = create_dna_string(mod_map)
        return fit

def create_dna_string(mod_map):
    dna = ""
    for mod_id in mod_map:
        mod = mod_map[mod_id]
        dna += str(mod[0]) + ";" + str(mod[1]) + ":"
    
    return dna+":" # dna always needs to end with 2 colons

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
        else:
            mod_count = 0
        mod_map[mod_id] = [mod_id, mod_count]
    
    return mod_map

def get_fit_format(line):
    # [Vindicator, VeniVindiVG]
    if re.match("\[.*,.*\]", line):
        return "eft"
    else:  # just consider everyhting else dna
        return "dna"

def get_item_id(name):
    logger.debug("Getting id for item %s", name)
    item = db.session.query(InvType).filter(InvType.typeName == name).first()
    if item == None:
        return -1
    return item.typeID
    
# load an account by its id
def get_account_from_db(int_id):
    return db.session.query(Account).filter(Account.id == int_id).first()

# load a character by its id
def get_char_from_db(int_id):
    return db.session.query(Character).filter(Character.id == int_id).first()

def create_new_character(eve_id, char_name):
    char = Character()
    char.id = eve_id
    char.eve_name = char_name
    char.newbro = True
    db.session.add(char)
    db.session.commit()
    return char

def get_character_by_name(eve_name):
    eve_id = get_character_id_from_name(eve_name)
    return get_character_by_id_and_name(eve_id, eve_name)

def get_character_by_id_and_name(eve_id, eve_name):
    char = get_char_from_db(eve_id);
    if char == None:
        # create a new char
        char = create_new_character(eve_id, eve_name)

    return char

def is_charid_banned(eve_id):
    if eve_id == 0: # this stands for no id in the eve api (for example no alliance)
        return False
    return db.session.query(Ban).filter(Ban.id == eve_id).count() == 1

def is_char_banned(char):
    reason = "Character"
    is_banned = char.banned
    if not is_banned:
        corp_id, alli_id = get_affiliation(char.get_eve_id())
        if (is_charid_banned(corp_id)):
            reason = "Corporation"
            is_banned = True
        elif is_charid_banned(alli_id):
            reason = "Alliance"
            is_banned = True

    return is_banned, reason

def is_igb():
    user_agent = request.headers.get('User-Agent')
    if user_agent == None:
        return False
    return ("EVE-IGB" in user_agent)


def get_character(user):
    if user.type == "account":
        return user.current_char_obj
    else:
        return user