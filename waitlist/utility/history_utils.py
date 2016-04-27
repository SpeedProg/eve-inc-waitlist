from waitlist.storage.database import HistoryEntry
def create_history_object(targetID, event_type, sourceID=None, fitlist=None):
    hEntry = HistoryEntry()
    hEntry.sourceID = sourceID
    hEntry.targetID = targetID
    hEntry.action = event_type
    if fitlist is not None:
        for fit in fitlist:
            hEntry.fittings.append(fit)
    return hEntry