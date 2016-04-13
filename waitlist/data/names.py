
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
    
    @staticmethod
    def get_role_list():
        return [WTMRoles.admin, WTMRoles.officer, WTMRoles.fc, WTMRoles.lm, WTMRoles.tbadge, WTMRoles.resident, WTMRoles.dev, WTMRoles.leadership]
    

DEFAULT_PREFIX = "default"