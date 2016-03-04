import string,random
import logging
import re
from waitlist.storage.database import Shipfit, InvType, session, Character
from flask_login import login_required, current_user
from waitlist.storage import database
from flask.globals import request

logger = logging.getLogger(__name__)

class LogMixin(object):
    @property
    def logger(self):
        name = '.'.join([__name__, self.__class__.__name__])
        return logging.getLogger(name)

def get_random_token(length):
    return unicode(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length)))

def parseEft(eftString):
        fit = Shipfit()
        lines = re.split('[\n\r]+', eftString)
        # take [Vindicator, VeniVindiVG] remove the [] and split at ,
        info = lines[0][1:-1].split(",", 1)

        ship_type = info[0]  # I only care about what ship it is

        ship_id = get_item_id(ship_type)
        fit.ship_type = ship_id
        
        for i in range(1, len(lines)):  # start with 2nd line since 1st is shiptype
            line = lines[i].strip()
            
            if not line:  # it is an empty line
                continue

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
    logger.info("Getting id for item %s", name)
    return session.query(InvType).filter(InvType.typeName == name).first().typeID

@login_required
def get_char_id():
    current_user.get_eve_id()
    
# load an account by its id
def get_account_from_db(int_id):
    return database.session.query(database.Account).filter(database.Account.id == int_id).first()

# load a character by its id
def get_char_from_db(int_id):
    return database.session.query(database.Character).filter(database.Character.id == int_id).first()

def create_new_character(eve_id, char_name):
    char = Character()
    char.id = eve_id
    char.eve_name = char_name
    database.session.add(char)
    return char

def is_igb():
    user_agent = request.headers.get('User-Agent')
    return ("EVE-IGB" in user_agent)