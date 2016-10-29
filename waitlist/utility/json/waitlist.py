def makeJsonWLEntry(entry, excludeFits = False, includeFitsFrom = None):
    return {
            'id': entry.id,
            'character': makeJsonCharacter(entry.user_data),
            'fittings': makeJsonFittings(entry.fittings, excludeFits, includeFitsFrom, entry.user),
            'time': entry.creation,
            'missedInvites': entry.inviteCount
            }

def makeJsonWL(dbwl, excludeFits = False, includeFitsFrom = None):
    return {
            'id': dbwl.id,
            'name': dbwl.name,
            'entries': makeEntries(dbwl.entries, excludeFits, includeFitsFrom)
    }

def makeJsonCharacter(dbcharacter):
    return {
            'id': dbcharacter.get_eve_id(),
            'name': dbcharacter.get_eve_name(),
            'newbro': dbcharacter.is_new()
            }

def makeJsonFitting(dbfitting):
    return {
            'id': dbfitting.id,
            'shipType': dbfitting.ship_type,
            'shipName': dbfitting.ship.typeName,
            'modules': dbfitting.modules,
            'comment': dbfitting.comment,
#            'dna': dbfitting.get_dna(),
            'wl_type': dbfitting.wl_type
        }

def makeJsonFittings(dbfittings, excludeFits = False, includeFitsFrom = None, charId = None):
    fittings = []
    if (excludeFits and (includeFitsFrom == None or charId == None)):
        return fittings

    for fit in dbfittings:
        if (not excludeFits or (charId in includeFitsFrom)):
            fittings.append(makeJsonFitting(fit))

    return fittings

def makeEntries(dbentries, excludeFits = False, includeFitsFrom = None):
    entries = []
    for entry in dbentries:
        entries.append(makeJsonWLEntry(entry, excludeFits, includeFitsFrom))
    return entries

def makeJsonGroups(groups):
    return [makeJsonGroup(grp) for grp in groups]

def makeJsonGroup(group):
    return {
        'groupID': group.groupID,
        'groupName': group.groupName,
        'groupDisplayName': group.displayName,#
        'influence': group.influence,
        'status': group.status,
        'enabled': group.enabled,
        'fcs': makeJsonFCs(group.fcs),
        'managers': makeJsonManagers(group),
        'station': makeJsonStation(group.dockup),
        'solarSystem': makeJsonSolarSystem(group.system),
        'constellation': makeJsonConstellation(group.constellation),
        'logiwlID': group.logiwlID,
        'dpswlID': group.dpswlID,
        'sniperwlID': group.sniperwlID,
        'otherwlID': group.otherwlID
        }

def makeJsonFCs(fcs):
    return [makeJsonFC(fc) for fc in fcs]

def makeJsonFC(fc):
    return makeJsonCharacter(fc.current_char_obj)

def makeJsonManagers(group):
    if len(group.fleets) > 0:
        return [makeJsonCharacter(fleet.comp) for fleet in group.fleets]
    else:
        return [makeJsonCharacter(manager.current_char_obj) for manager in group.manager]

def makeJsonSolarSystem(system):
    if system is None:
        return None
    return {
        'solarSystemID': system.solarSystemID,
        'solarSystemName': system.solarSystemName
        }

def makeJsonConstellation(constellation):
    if constellation is None:
        return None
    return {
        'constellationID': constellation.constellationID,
        'constellationName': constellation.constellationName
        }

def makeJsonStation(station):
    if station is None:
        return None
    return {
        'stationID': station.stationID,
        'stationName': station.stationName
        }

def makeJsonWaitlistsBaseData(waitlists):
    return [makeJsonWaitlistBaseData(l) for l in waitlists]

def makeJsonWaitlistBaseData(waitlist):
    return {
        'id': waitlist.id,
        'name': waitlist.name,
        'entryCount': len(waitlist.entries)
    }