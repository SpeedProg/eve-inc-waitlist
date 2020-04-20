from typing import Optional, Sequence

from waitlist.storage.database import Waitlist, Character, Shipfit, WaitlistGroup, SolarSystem, Constellation, Station,\
    Account

Optionalcharids = Optional[Sequence[int]]


def make_json_wl_entry(entry, exclude_fits: bool = False, include_fits_from: Optionalcharids = None,
                       scramble_names: bool = False, include_names_from: Optionalcharids = None):
    response = {
        'id': entry.id,
        'character': make_json_character(entry.user_data, scramble_names=scramble_names,
                                         include_names_from=include_names_from),
        'time': entry.creation,
        'missedInvites': entry.inviteCount
    }

    if not (exclude_fits and ((include_fits_from is None or entry.user is None) or entry.user not in include_fits_from)):
        response['fittings'] = list(map(make_json_fitting, entry.fittings))

    return response


def make_json_wl(dbwl: Waitlist, exclude_fits: bool = False, include_fits_from: Optionalcharids = None,
                 scramble_names: bool = False, include_names_from: Optionalcharids = None):
    return {
        'id': dbwl.id,
        'name': dbwl.name,
        'entries': make_entries(dbwl.entries, exclude_fits, include_fits_from, scramble_names=scramble_names,
                                include_names_from=include_names_from)
    }


def make_json_character(dbcharacter: Character, scramble_names: bool = False,
                        include_names_from: Optionalcharids = None):
    return {
        'id': dbcharacter.get_eve_id() if not scramble_names or (
            include_names_from is not None and dbcharacter.get_eve_id() in include_names_from) else None,
        'name': dbcharacter.get_eve_name() if not scramble_names or (
            include_names_from is not None and dbcharacter.get_eve_id() in include_names_from) else 'Name Hidden',
        'newbro': dbcharacter.is_new
    }


def make_json_fitting(dbfitting: Shipfit):
    return {
        'id': dbfitting.id,
        'shipType': dbfitting.ship_type,
        'shipName': dbfitting.ship.typeName,
        'modules': dbfitting.modules,
        'comment': dbfitting.comment,
        #            'dna': dbfitting.get_dna(),
        'wl_type': dbfitting.wl_type
    }


def make_entries(dbentries, exclude_fits: bool = False, include_fits_from: Optionalcharids = None,
                 scramble_names: bool = False, include_names_from: Optionalcharids = None):
    entries = []
    for entry in dbentries:
        entries.append(make_json_wl_entry(entry, exclude_fits, include_fits_from, scramble_names,
                                          include_names_from=include_names_from))
    return entries


def make_json_groups(groups: Sequence[WaitlistGroup]):
    return [make_json_group(grp) for grp in groups]


def make_json_group(group: WaitlistGroup):
    return {
        'groupID': group.groupID,
        'groupName': group.groupName,
        'groupDisplayName': group.displayName,  #
        'influence': group.influence,
        'status': group.status,
        'enabled': group.enabled,
        'fcs': make_json_fcs(group.fcs),
        'managers': make_json_managers(group),
        'station': make_json_station(group.dockup),
        'solarSystem': make_json_solar_system(group.system),
        'constellation': make_json_constellation(group.constellation),
        'logiwlID': None if group.logilist is None else group.logilist.id,
        'dpswlID': None if group.dpslist is None else group.dpslist.id,
        'sniperwlID': None if group.sniperlist is None else group.sniperlist.id,
        'otherwlID': None if group.otherlist is None else group.otherlist.id,
        'xupwlID': None if group.xuplist is None else group.xuplist.id
    }


def make_json_fcs(fcs: Sequence[Account]):
    return [make_json_fc(fc) for fc in fcs if fc.current_char_obj is not None]


def make_json_fc(fc: Account):
    return make_json_character(fc.current_char_obj)


def make_json_managers(group: WaitlistGroup):
    if len(group.fleets) > 0:
        return [make_json_character(fleet.comp.current_char_obj) for fleet in group.fleets if fleet.comp is not None and fleet.comp.current_char_obj is not None]
    else:
        return [make_json_character(manager.current_char_obj) for manager in group.manager if manager.current_char_obj is not None]


def make_json_solar_system(system: SolarSystem):
    if system is None:
        return None
    return {
        'solarSystemID': system.solarSystemID,
        'solarSystemName': system.solarSystemName
    }


def make_json_constellation(constellation: Constellation):
    if constellation is None:
        return None
    return {
        'constellationID': constellation.constellationID,
        'constellationName': constellation.constellationName
    }


def make_json_station(station: Station):
    if station is None:
        return None
    return {
        'stationID': station.stationID,
        'stationName': station.stationName
    }


def make_json_waitlists_base_data(waitlists: Sequence[Waitlist]):
    return [make_json_waitlist_base_data(l) for l in waitlists]


def make_json_waitlist_base_data(waitlist: Waitlist):
    return {
        'id': waitlist.id,
        'name': waitlist.name,
        'groupID': waitlist.group.groupID,
        'entryCount': len(waitlist.entries)
    }
