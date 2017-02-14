from typing import Optional, Sequence

from waitlist.storage.database import HistoryEntry, Shipfit


def create_history_object(target_id: int, event_type: str, source_id: Optional[int] = None,
                          fitlist: Optional[Sequence[Shipfit]] = None) -> HistoryEntry:
    h_entry = HistoryEntry()
    h_entry.sourceID = source_id
    h_entry.targetID = target_id
    h_entry.action = event_type
    if fitlist is not None:
        for fit in fitlist:
            h_entry.fittings.append(fit)
    return h_entry
