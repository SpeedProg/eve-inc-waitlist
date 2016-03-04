
class WaitlistNames():
    logi = "logi"
    dps = "dps"
    sniper = "sniper"
    
class WTMRoles():
    admin = "admin"
    officer = "officer"
    fc = "fc"
    lm = "lm"
    tbadge = "tbadge"
    resident = "resident"
    
    @staticmethod
    def get_role_list():
        return [WTMRoles.admin, WTMRoles.officer, WTMRoles.fc, WTMRoles.lm, WTMRoles.tbadge, WTMRoles.resident]