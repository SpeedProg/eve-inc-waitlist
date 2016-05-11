import logging
from waitlist.base import db
from waitlist.storage.database import Setting
logger = logging.getLogger(__name__)

def get(setting_name):
    setting = db.session.query(Setting).get(setting_name)
    if setting == None:
        return None
    else:
        return setting.value

def get_int(setting_name):
    set_str = get(setting_name)
    if set_str is None:
        return None
    else:
        return int(set_str)

def save(setting_name, value):
    setting = Setting(key=setting_name, value=value)
    db.session.merge(setting)
    db.session.commit()

def remove_setting(setting_name):
    db.session.query(Setting).filter(Setting.key == setting_name).delete()
    db.session.commit()
    

def sget_active_ts_id():
    return get_int("active_ts")

def sset_active_ts_id(tsID):
    if tsID is None:
        remove_setting("active_ts")
    else:
        save("active_ts", str(tsID))