from waitlist.utility.constants import location_flags, effects
from typing import List, Dict, Optional
from waitlist.storage.database import InvType, Shipfit, FitModule
from waitlist import db
import logging
import re
from waitlist.utility.eve_id_utils import get_item_id

logger = logging.getLogger(__name__)


def parse_eft(lines: List[str]) -> Shipfit:
        slot_list: List[Dict[int, List[int]]] = [dict(), dict(), dict(),
                                                 dict(), dict(), dict(),
                                                 dict()]
        if len(lines) < 2:
            return None

        fit = Shipfit()
        # take [Vindicator, VeniVindiVG] remove the [] and split at ,
        info = lines[0][1:-1].split(",", 1)
        if len(info) < 2:
            return None

        ship_type = info[0]  # I only care about what ship it is

        ship_id = get_item_id(ship_type)
        if ship_id == -1:
            return None
        fit.ship_type = ship_id

        # the 2nd line is empty if it is a pyfa fit!
        # the 2nd line has something if it is ingame fit!
        second_line = lines[1].strip()

        is_pyfa = ((not second_line) or second_line == '')

        # the cargo slot there twice because ingame client
        # does 2 empty lines after subystem and before dronebay
        # and pyfa only does 1
        # so now with pyfa
        sections = [location_flags.LOW_SLOT, location_flags.MID_SLOT,
                    location_flags.HIGH_SLOT, location_flags.RIG_SLOT,
                    location_flags.SUBYSTEM_SLOT, location_flags.DRONEBAY_SLOT,
                    location_flags.CARGO_SLOT]

        section_idx = 0  # 'low'
        # used to store a list of items
        # that we want to remember we created
        # start at 3rd line for pyfa and at 2nd for ingame
        i = 2 if is_pyfa else 1
        while i < len(lines):

            line = lines[i].strip()
            logger.info('SectionIdx: %d Line: %s', section_idx, line)
            # an empty line indicates changing to the next section
            if not line or line == '':
                section_idx = section_idx + 1
                # to reach this ingame fit needs 2 new lines
                # pyfa fit only 1
                if section_idx == location_flags.DRONEBAY_SLOT:
                    # if we are on ingame fit and next line is empty
                    # skip next line (ingame has 2 newline before drones
                    if not is_pyfa:
                        next_line = lines[i+1].strip()
                        if not next_line or next_line == '':
                            i += 1

                i += 1
                continue

            # check if it is an empty slot
            if re.match("\[[\w\s]+\]$", line):
                i += 1
                continue

            # check if it contains a xNUMBER and is by that drone or cargo
            is_cargo = re.match(".*x\d+$", line) is not None
            logger.debug("%s is_cargo = %s", line, is_cargo)

            if sections[section_idx] == location_flags.CARGO_SLOT:
                mod_info = line.rsplit(" x", 2)
                mod_name = mod_info[0]
                mod_amount = int(mod_info[1])
            elif sections[section_idx] == location_flags.DRONEBAY_SLOT:
                # because of how pyfa and ingame format are different
                # we might endup here while really being in cargo...
                mod_info = line.rsplit(" x", 2)
                mod_name = mod_info[0]
                mod_amount = int(mod_info[1])
            else:
                if line.endswith("/OFFLINE"):
                    line = line[:-8]
                # might contain charge after a ', ' we can ignore this
                name_parts = line.split(", ")
                mod_name = name_parts[0]
                mod_amount = 1

            mod_id = get_item_id(mod_name)
            if mod_id == -1:  # items was not in database
                i += 1
                continue

            if sections[section_idx] == location_flags.DRONEBAY_SLOT:
                # check here if this item is really a drone
                inv_type: InvType = db.session.query(InvType).get(mod_id)
                if not inv_type.IsDrone:
                    # if this is no drone, we 100% where in cargo
                    # and this was no ingame export
                    # move the collected data to the cargo slot
                    mod_map = slot_list[sections[section_idx]]
                    slot_list[sections[section_idx]] = dict()
                    slot_list[location_flags.CARGO_SLOT] = mod_map
                    # and change our index
                    section_idx = 6

            mod_map = slot_list[sections[section_idx]]

            if mod_id in mod_map:
                mod_entry = mod_map[mod_id]
            else:  # if the module is not in the map create it
                mod_entry = [mod_id, 0]
                mod_map[mod_id] = mod_entry

            mod_entry[1] += mod_amount
            i += 1

        for idx, mod_map in enumerate(slot_list):
            for modid in mod_map:
                mod = mod_map[modid]
                # lets set amounts to max signed int,
                # because it is not really imporant
                # some one was manually making those values up anyway
                if mod[1] > 2147483647 or mod[1] < 0:
                    mod[1] = 2147483647

                # lets check the value actually exists
                inv_type = db.session.query(InvType).get(mod[0])
                if inv_type is None:
                    raise ValueError('No module with ID='+str(mod[0]))

                db_module = FitModule(moduleID=mod[0], locationFlag=idx,
                                      amount=mod[1])
                fit.moduleslist.append(db_module)

        fit.modules = create_dna_string(slot_list)

        return fit


def create_dna_string(slot_list: List[Dict[int, List[int]]]):
    dna = ''
    # last one would be chage but it doesn't exist in EFT format
    # charges are contained under cargo together with other items
    dna_order = [location_flags.SUBYSTEM_SLOT, location_flags.HIGH_SLOT,
                 location_flags.MID_SLOT, location_flags.LOW_SLOT,
                 location_flags.RIG_SLOT, location_flags.DRONEBAY_SLOT]
    for slot_id in dna_order:
        mod_map = slot_list[slot_id]
        sub_dna = ''
        for mod_id in mod_map:
            mod = mod_map[mod_id]
            sub_dna += str(mod[0]) + ';' + str(mod[1]) + ':'

        dna += sub_dna

    # now handle cargo
    mod_map = slot_list[location_flags.CARGO_SLOT]
    sub_dna_charges = ''
    sub_dna_modules = ''
    for mod_id in mod_map:
        mod = mod_map[mod_id]
        # get type info
        inv_type: InvType = db.session.query(InvType).get(mod[0])
        if inv_type is None:
            logger.error("There was no inventory type for id=%d found.",
                         mod[0])
            continue

        if inv_type.IsCharge:
            sub_dna_charges += str(mod[0]) + ";" + str(mod[1]) + ":"
        else:
            # modules in cargo need this postfix behind the id
            sub_dna_modules += str(mod[0]) + '_' + ";" + str(mod[1]) + ":"
    dna = dna + sub_dna_charges + sub_dna_modules
    if dna == "":  # if there is no module
        return ":"
    return dna+":"  # dna always needs to end with 2 colons%


# map looks like this mod_map = {mod_id:[mod_id,mod_count],...}
def parse_dna_fitting(dna_string: str) -> List[Dict[int, List[int]]]:
    """
    Create a list of modules in specific locations from the given dna string
    locations use location_flags as list index
    This does not support a full DNA string only the part after shiptype id:
    """
    slot_list: List[Dict[int, List[int]]] = [dict(), dict(), dict(),
                                             dict(), dict(),
                                             dict(), dict()]
    mods = dna_string.split(':')
    for mod in mods:
        if not mod:
            continue
        parts = mod.split(";")
        is_cargo_module = parts[0].endswith('_')
        if is_cargo_module:
            parts[0] = parts[0][0:-1]

        mod_id = int(parts[0])
        if len(parts) > 1:
            mod_count = int(parts[1])
            if mod_count > 2147483647 or mod_count < 0:
                raise ValueError("Mod amount is out of range of signed int")
        else:
            raise ValueError("Mod did not contain an amount")

        inv_type = db.session.query(InvType).get(mod_id)
        if inv_type is None:
            raise ValueError("InvType with id=" + mod_id + " not found")

        location_flag = get_location_flag(inv_type)
        if location_flag is None:
            logger.error("No locationflag found for InvType with typeID=%d",
                         inv_type.typeID)
            continue

        mod_map = slot_list[location_flag]
        if mod_id in mod_map:
            mod_data = mod_map[mod_id]
            mod_data[1] += mod_count
        else:
            mod_map[mod_id] = [mod_id, mod_count]

    return slot_list


def get_location_flag(inv_type: InvType) -> Optional[int]:
    """Returns the value for a slot or none if no slot
    """
    if inv_type.IsCharge or inv_type.IsBooster:
        return location_flags.CARGO_SLOT
    if inv_type.IsDrone:
        return location_flags.DRONEBAY_SLOT
    for dogma_effect in inv_type.dogma_effects:
        if dogma_effect.effectID == effects.POWER_SLOT_HIGH:
            return location_flags.HIGH_SLOT
        if dogma_effect.effectID == effects.POWER_SLOT_MED:
            return location_flags.MID_SLOT
        if dogma_effect.effectID == effects.POWER_SLOT_LOW:
            return location_flags.LOW_SLOT
        if dogma_effect.effectID == effects.POWER_SLOT_RIG:
            return location_flags.RIG_SLOT
        if dogma_effect.effectID == effects.POWER_SLOT_SUBSYSTEM:
            return location_flags.SUBYSTEM_SLOT
    return None


def get_fit_format(line):
    # [Vindicator, VeniVindiVG]
    if re.match("\[.*,.*\]", line):
        return "eft"
    else:  # just consider everyhting else dna
        return "dna"
