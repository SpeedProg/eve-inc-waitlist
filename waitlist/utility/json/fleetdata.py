
import json
from datetime import datetime

from waitlist.utility.swagger.eve.fleet.models import FleetMember


class FleetMemberEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FleetMember):
            return obj.data
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
