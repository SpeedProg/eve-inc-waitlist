
class WaitlistNames():
    logi = "logi"
    dps = "dps"
    sniper = "sniper"
    xup_queue = "queue"
    other = "other"
    
class WTMRoles():
    admin = "admin"
    officer = "officer"
    fc = "fc"
    lm = "lm"
    tbadge = "tbadge"
    resident = "resident"
    dev = "developer"
    leadership = "leadership"
    mod_mail_resident = "mod_mail_res"
    mod_mail_tbadge = "mod_mail_tbadge"
    send_mail_tbadge = "send_mail_tbadge"
    send_mail_resident = "send_mail_resident"
    
    @staticmethod
    def get_role_list():
        return [WTMRoles.admin, WTMRoles.officer, WTMRoles.fc, WTMRoles.lm, WTMRoles.tbadge, WTMRoles.resident, WTMRoles.dev, WTMRoles.leadership,
                WTMRoles.mod_mail_resident, WTMRoles.mod_mail_tbadge]
    

DEFAULT_PREFIX = "default"