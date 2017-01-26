import json
from pycrest.eve import APIObject
class FleetMemberEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, APIObject):
            return obj._dict
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)