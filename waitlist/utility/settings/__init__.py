import logging
from waitlist.base import db
from waitlist.storage.database import Setting
logger = logging.getLogger(__name__)


def get(setting_name):
    setting = db.session.query(Setting).get(setting_name)
    if setting is None:
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


def sget_resident_mail():
    return get("mail_resident")


def sset_resident_mail(text):
    save("mail_resident", text)


def sget_resident_topic():
    return get("mail_resident_topic")


def sset_resident_topic(text):
    save("mail_resident_topic", text)


def sget_tbadge_mail():
    return get("mail_tbadge")


def sset_tbadge_mail(text):
    save("mail_tbadge", text)


def sget_tbadge_topic():
    return get("mail_tbadge_topic")


def sset_tbadge_topic(text):
    save("mail_tbadge_topic", text)


def sget_other_mail():
    return get("mail_other")


def sset_other_mail(text):
    save("mail_other", text)


def sget_other_topic():
    return get("mail_other_topic")


def sset_other_topic(text):
    save("mail_other_topic", text)


def sget_motd_hq():
    return get("motd_hq")


def sset_motd_hq(text):
    save("motd_hq", text)


def sget_motd_vg():
    return get("motd_vg")


def sset_motd_vg(text):
    save("motd_vg", text)


def sget_insert(name):
    return get('insert_'+name)


def sset_insert(name, text):
    return save('insert_'+name, text)


def sget_active_coms_id() -> str:
    return get('active_coms_id')


def sset_active_coms_id(coms_id) -> None:
    if coms_id is None:
        remove_setting('active_coms_id')
    else:
        save('active_coms_id', str(coms_id))


def sget_active_coms_type():
    return get('active_coms_type')


def sset_active_coms_type(coms_type: str) -> None:
    if coms_type is None:
        remove_setting('active_coms_type')
    else:
        save('active_coms_type', coms_type)

