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

def makeHistoryJson(entries):
    return {'history': [makeHistoryEntryJson(entry) for entry in entries]}

def makeHistoryEntryJson(entry):
    return {'historyID': entry.historyID,
    'action': entry.action,
    'time': entry.time,
    'exref': entry.exref,
    'fittings': [makeJsonFitting(fit) for fit in entry.fittings],
    'source': None if entry.source is None else makeJsonAccount(entry.source),
    'target': makeJsonCharacter(entry.target)
    }

def makeJsonAccount(acc):
    return {'id': acc.id,
            'character': makeJsonCharacter(acc.current_char_obj),
            'username': acc.username,
    }