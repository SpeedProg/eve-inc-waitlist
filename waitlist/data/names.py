
class WaitlistNames():
    logi = "logi"
    dps = "dps"
    sniper = "sniper"
    xup_queue = "queue"
    
class WTMRoles():
    admin = "admin"
    officer = "officer"
    fc = "fc"
    lm = "lm"
    tbadge = "tbadge"
    resident = "resident"
    dev = "developer"
    
    @staticmethod
    def get_role_list():
        return [WTMRoles.admin, WTMRoles.officer, WTMRoles.fc, WTMRoles.lm, WTMRoles.tbadge, WTMRoles.resident, WTMRoles.dev]