
import json
from waitlist.utility.swagger.eve.fleet.models import FleetMember


class FleetMemberEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FleetMember):
            return obj._data
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)