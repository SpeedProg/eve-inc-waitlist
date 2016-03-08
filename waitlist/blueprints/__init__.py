import gevent
subscriptions = []

def send_invite_notice(data):
    def notify():
        for sub in subscriptions:
            sub.put(data)

    gevent.spawn(notify)