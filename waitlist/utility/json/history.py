from waitlist.utility.json.waitlist import make_json_fitting, make_json_character


def make_json_account(acc):
    return {'id': acc.id,
            'character': make_json_character(acc.current_char_obj),
            'username': acc.username,
            }


def make_history_json(entries):
    return {'history': [make_history_entry_json(entry) for entry in entries]}


def make_history_entry_json(entry):
    return {
        'historyID': entry.historyID,
        'action': entry.action,
        'time': entry.time,
        'exref': entry.exref,
        'fittings': [make_json_fitting(fit) for fit in entry.fittings],
        'source': None if entry.source is None else make_json_account(entry.source),
        'target': make_json_character(entry.target)
    }
