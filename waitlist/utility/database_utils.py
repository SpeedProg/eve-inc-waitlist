from waitlist.storage.database import Shipfit, InvType, FitModule
from waitlist.utility.eve_id_utils import get_item_id
import logging
import re
from waitlist.utility.utils import create_dna_string
from waitlist import db

logger = logging.getLogger(__name__)


def parse_eft(lines):
        fit = Shipfit()
        # take [Vindicator, VeniVindiVG] remove the [] and split at ,
        info = lines[0][1:-1].split(",", 1)

        ship_type = info[0]  # I only care about what ship it is

        ship_id = get_item_id(ship_type)
        fit.ship_type = ship_id

        mod_map = {}
        for i in range(1, len(lines)):

            line = lines[i].strip()
            if not line:
                continue
            
            # check if it is an empty slot
            if re.match("\[[\w\s]+\]$", line):
                continue
            
            # check if it contains a xNUMBER and is by that drone or cargo
            is_cargo = re.match(".*x\d+$", line) is not None
            logger.debug("%s is_cargo = %s", line, is_cargo)

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
            if mod_id == -1:  # items was not in database
                    continue
            
            if mod_id in mod_map:
                mod_entry = mod_map[mod_id]
            else:  # if the module is not in the map create it
                
                mod_entry = [mod_id, 0]
                mod_map[mod_id] = mod_entry
            
            mod_entry[1] += mod_amount

        for modid in mod_map:
            mod = mod_map[modid]
            # lets set amounts to max signed int, because it is not really imporant
            # some one was manually making those values up anyway
            if mod[1] > 2147483647 or mod[1] < 0:
                mod[1] = 2147483647
            
            # lets check the value actually exists
            module = db.session.query(InvType).get(mod[0])
            if module is None:
                raise ValueError('No module with ID='+str(mod[0]))
            
            db_module = FitModule(moduleID=mod[0], amount=mod[1])
            fit.moduleslist.append(db_module)
        
        fit.modules = create_dna_string(mod_map)

        return fit
