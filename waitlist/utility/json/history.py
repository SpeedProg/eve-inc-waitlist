'''
Created on 29.10.2016

@author: SpeedProg
'''
from __future__ import absolute_import
import waitlist.utility.json

def makeJsonAccount(acc):
    return {'id': acc.id,
            'character': makeJsonCharacter(acc.current_char_obj),
            'username': acc.username,
    }

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