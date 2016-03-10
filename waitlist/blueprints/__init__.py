import gevent
from waitlist.blueprints.settings import FleetStatus
subscriptions = []
fleet_status = FleetStatus()

def send_invite_notice(data):
    def notify():
        for sub in subscriptions:
            sub.put(data)

    gevent.spawn(notify)