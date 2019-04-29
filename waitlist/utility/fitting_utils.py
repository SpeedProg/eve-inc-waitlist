import operator
from decimal import Decimal
from sqlalchemy import literal
from waitlist.utility.constants import location_flags, effects, check_types
from typing import List, Dict, Optional, Tuple, AbstractSet, Union
from waitlist.storage.database import InvType, Shipfit, FitModule,\
    MarketGroup, ShipCheckCollection, ShipCheck, Waitlist, InvGroup
from waitlist.base import db
from waitlist.data.names import WaitlistNames
import logging
import re
from waitlist.utility.eve_id_utils import get_item_id

logger = logging.getLogger(__name__)


def parse_eft(lines: List[str]) -> Shipfit:
    slot_list: List[Dict[int, List[int]]] = [dict(), dict(), dict(),
                                             dict(), dict(), dict(),
                                             dict(), dict()]
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
                location_flags.CARGO_SLOT, location_flags.FIGHTERS_SLOT]

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

        # check if it contains a xNUMBER and is by that drone/fighter or cargo
        is_cargo = re.match(".*x\d+$", line) is not None
        logger.debug("%s is_cargo = %s", line, is_cargo)

        if sections[section_idx] == location_flags.CARGO_SLOT:
            mod_info = line.rsplit(" x", 2)
            mod_name = mod_info[0]
            mod_amount = int(mod_info[1])
        elif sections[section_idx] in [location_flags.DRONEBAY_SLOT,
                                       location_flags.FIGHTERS_SLOT]:
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
                section_idx = location_flags.CARGO_SLOT

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
    logger.debug('SlotList: %r', slot_list)
    fit.modules = create_dna_string(slot_list)

    return fit


def create_dna_string(slot_list: List[Dict[int, List[int]]]):
    dna = ''
    # last one would be chage but it doesn't exist in EFT format
    # charges are contained under cargo together with other items
    dna_order = [location_flags.SUBYSTEM_SLOT, location_flags.HIGH_SLOT,
                 location_flags.MID_SLOT, location_flags.LOW_SLOT,
                 location_flags.RIG_SLOT, location_flags.DRONEBAY_SLOT,
                 location_flags.FIGHTERS_SLOT]
    for slot_id in dna_order:
        logger.debug('SLOTID: %d', slot_id)
        mod_map = slot_list[slot_id]
        sub_dna = ''
        for mod_id in mod_map:
            mod = mod_map[mod_id]
            logger.debug('ModId: %d ModAmount: %d', mod[0], mod[1])
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
                                             dict(), dict(), dict()]
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

        if is_cargo_module:
            location_flag = location_flags.CARGO_SLOT
        else:
            inv_type = db.session.query(InvType).get(mod_id)
            if inv_type is None:
                raise ValueError("InvType with id=" + mod_id + " not found")

            location_flag = get_location_flag(inv_type)
            if location_flag is None:
                logger.error("No locationflag found for"
                             + " InvType with typeID=%d",
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
    if inv_type.IsFighter:
        return location_flags.FIGHTERS_SLOT

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


def get_waitlist_type_for_ship_type(checks: List[ShipCheck], ship_type_id: int) -> Optional[Tuple[str, int]]:
    """ Get a tag, waitlist id tuple or None if no check applies
    """
    logger.debug('Got ship_type %d', ship_type_id)

    ship_type: InvType = db.session.query(InvType).get(ship_type_id)
    # collect market groups
    market_group_ids = []
    m_group: MarketGroup = ship_type.market_group
    while m_group is not None:
        market_group_ids.append(m_group.marketGroupID)
        m_group = m_group.parent
    logger.debug('Found marketgroups: %r', market_group_ids)

    for check in checks:
        logger.debug('Doing Check %s of type  %d', check.checkName, check.checkType)
        if check.checkType == check_types.SHIP_CHECK_TYPEID:
            if db.session.query(check.check_types.filter(InvType.typeID == ship_type.typeID).exists()).scalar():
                return check.checkTag, check.checkTargetID
        elif check.checkType == check_types.SHIP_CHECK_INVGROUP:
            if db.session.query(check.check_groups.filter(InvGroup.groupID == ship_type.groupID).exists()).scalar():
                return check.checkTag, check.checkTargetID
        elif check.checkType == check_types.SHIP_CHECK_MARKETGROUP:
            if db.session.query(check.check_market_groups.filter(MarketGroup.marketGroupID.in_(market_group_ids)).exists()).scalar():
                return check.checkTag, check.checkTargetID
    logger.debug('No match found for ship_type')
    return None

def get_market_groups(inv_type: InvType) -> List[int]:
    group_ids: List[int] = []
    m_group: MarketGroup = inv_type.market_group
    while m_group is not None:
        group_ids.append(m_group.marketGroupID)
        m_group = m_group.parent
    return group_ids


def does_check_apply(check: ShipCheck, ship_type_id: int) -> bool:
    invtype: InvType = db.session.query(InvType).get(ship_type_id)
    has_restriction = False
    if len(check.check_rest_types) > 0:
        has_restriction = True
        for itype in check.check_rest_types:
            if itype.typeID == ship_type_id:
                return True
    if len(check.check_rest_groups) > 0:
        has_restriction = True
        for igroup in checks.check_rest_groups:
            if igroup.groupID == invtype.groupID:
                return True
    market_groups = get_market_groups(invtype)
    if len(check.check_rest_market_groups) > 0:
        has_restriction = True
        for mgroup in checks.check_rest_market_groups:
            if mgroup.marketGroupID in market_groups:
                return True

    return not has_restriction

def get_waitlist_type_for_modules(checks: List[ShipCheck], fit: Shipfit) -> Optional[Tuple[int, Tuple[Decimal, AbstractSet[str]]]]:
    """Get a tuple of module type id, amount, set of tags for the module with the highest value
    Or None if no check applied
    """
    logger.debug('Doing modules check with checks %r', checks)
    mod_list: List[Dict[int, Tuple(int, int)]] = parse_dna_fitting(fit.modules)
    high_slot_modules = mod_list[location_flags.HIGH_SLOT]
    logger.debug('Module list %r', mod_list)
    mod_ids = [mod_id for mod_id in high_slot_modules]
    logger.debug('Moudle ids: %r', mod_ids)
    # prepare marketgroup list for every module, we need it later on
    market_groups = dict()
    for mod_id in mod_ids:
        if mod_id not in market_groups:
            invtype: InvType = db.session.query(InvType).get(mod_id)
            market_groups[mod_id] = get_market_groups(invtype)

    logger.debug('Market groups: %r', market_groups)
    # for modules we need to hit every module once or never
    # never only if there is no rule for it!
    # so after getting a rule hit on a module, remove the module
    result_count_map: Dict[int, List[Union[Decimal, Set[str]]]] = dict()
    for check in checks:
        # lets see if this check applies to this ship
        if not does_check_apply(check, fit.ship_type):
            continue

        logger.debug('Doing check %s with type %d and target %s and mods %r', check.checkName, check.checkType, check.checkTarget.waitlistType, mod_ids)
        if check.checkTargetID not in result_count_map:
            result_count_map[check.checkTargetID] = [Decimal("0.00"), set()]
        modifier = Decimal("1.00") if check.modifier is None else check.modifier
        if check.checkType == check_types.MODULE_CHECK_TYPEID:
            remaining_mods = []
            type_ids = {type_obj.typeID for type_obj in check.check_types}
            logger.debug('Matching TypeIDs: %r', type_ids)
            for mod_id in mod_ids:
                if mod_id in type_ids:
                    logger.debug('Match found for %d', mod_id)
                    result_count_map[check.checkTargetID][0] += Decimal(high_slot_modules[mod_id][1]) * modifier
                    result_count_map[check.checkTargetID][1].add(check.checkTag)
                else:
                    remaining_mods.append(mod_id)
            mod_ids = remaining_mods
        elif check.checkType == check_types.MODULE_CHECK_MARKETGROUP:
            remaining_mods = []
            group_ids = {group_obj.marketGroupID for group_obj in check.check_market_groups}
            logger.debug('Market Groups for check: %r', group_ids)
            for mod_id in mod_ids:
                mgs_for_mod = set(market_groups[mod_id])
                logger.debug('MarketGroups for Mod %d are %r', mod_id, mgs_for_mod)
                if len(mgs_for_mod.intersection(group_ids)) > 0:
                    result_count_map[check.checkTargetID][0] += Decimal(high_slot_modules[mod_id][1]) * modifier
                    result_count_map[check.checkTargetID][1].add(check.checkTag)
                else:
                    remaining_mods.append(mod_id)
            mod_ids = remaining_mods
    logger.debug('Result Map: %r', result_count_map)
    return max(result_count_map.items(), key=lambda tpl: tpl[1][0], default=None)

def get_waitlist_type_for_fit(fit: Shipfit, waitlist_group_id: int) -> Tuple[str, int]:
    """Get a tag, waitlist_id tuple for this fit
    """
    # modlist[SLOT_INDEX][TYPE_ID][TYPE_ID][AMOUNT]
    logger.debug('Check fit %r against rules for group %d', fit, waitlist_group_id)
    check_collection: ShipCheckCollection = db.session.query(ShipCheckCollection).filter(
        ShipCheckCollection.waitlistGroupID == waitlist_group_id
    ).one()

    """
    This should work by:
      * Checks with same priority for modules are done in 1 go
      * For Ship Type and Module checks with same priority the module check is done before the shiptype
    """
    # we build a list of checks to execute
    # List[Tuple[module_checks, ship_checks]]
    checks_list: List[Tuple[List[ShipCheck], List[ShipCheck]]] = []
    current_order = None
    module_checks = None
    ship_type_checks = None
    for check in check_collection.checks:
        if current_order is None:
            current_order = check.order
            module_checks = []
            ship_type_checks = []
        elif current_order < check.order:
            current_order = check.order
            checks_list.append((
                module_checks,
                ship_type_checks
            ))
            module_checks = []
            ship_type_checks = []

        if check.checkType in [check_types.MODULE_CHECK_MARKETGROUP, check_types.MODULE_CHECK_TYPEID]:
            module_checks.append(check)
        elif check.checkType in [check_types.SHIP_CHECK_INVGROUP, check_types.SHIP_CHECK_TYPEID, check_types.SHIP_CHECK_MARKETGROUP]:
            ship_type_checks.append(check)

    # add the lowest priorty checks those do not get added by the for loop
    checks_list.append((module_checks, ship_type_checks))

    logger.debug("Check Structure: %r", checks_list)

    ship_wl_id = None
    tag = None
    for check_tuple in checks_list:
        module_data: Optional[Tuple[int, Tuple[Decimal, AbstractSet[str]]]] = get_waitlist_type_for_modules(check_tuple[0], fit)
        if module_data is not None and module_data[1][0] >= Decimal("4.00"):
            ship_wl_id = module_data[0]
            if len(module_data[1][1]) > 0:
                tag = module_data[1][1].pop()
            break
        ship_data = get_waitlist_type_for_ship_type(check_tuple[1], fit.ship_type)
        if ship_data is not None:
            tag = ship_data[0]
            ship_wl_id = ship_data[1]
            break

    if ship_wl_id is None:
        ship_wl_id = check_collection.defaultTarget.id
    if tag is None:
        tag = check_collection.defaultTag

    return tag, ship_wl_id

