
class WaitlistNames():
    logi = "logi"
    dps = "dps"
    sniper = "sniper"
    
class WTMRoles():
    admin = "admin"
    officer = "officer"
    fc = "fc"
    lm = "lm"
    tbag = "tbag"
    resident = "resident"
    
    @staticmethod
    def get_role_list():
        return [WTMRoles.admin, WTMRoles.officer, WTMRoles.fc, WTMRoles.lm, WTMRoles.tbag, WTMRoles.resident]