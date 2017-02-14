

class WaitlistNames:
    logi = "logi"
    dps = "dps"
    sniper = "sniper"
    xup_queue = "queue"
    other = "other"


class WTMRoles:
    admin = "admin"
    officer = "officer"
    fc = "fc"
    lm = "lm"
    tbadge = "tbadge"
    resident = "resident"
    dev = "developer"
    leadership = "leadership"
    
    ct = "Certified FC Trainer"
    clt = "Certified LM Trainer"
    af = "Active Founder"
    tct = "Training Certified FC Trainer"
    tclt = "Training Certified LM Trainer" 
    
    mod_mail_resident = "mod_mail_res"
    mod_mail_tbadge = "mod_mail_tbadge"
    send_mail_tbadge = "send_mail_tbadge"
    send_mail_resident = "send_mail_resident"

    dnames = dict([
        (admin, "Admin"),
        (officer, "Officer"),
        (fc, "Fleet Commander"),
        (lm, "Logi Master"),
        (tbadge, "Training Fleet Commander"),
        (resident, "Resident"),
        (dev, "Developer"),
        (leadership, "Leadership"),
        (ct, "Certified FC Trainer"),
        (clt, "Certified LM Trainer"),
        (af, "Active Founder"),
        (tct, "Training Certified FC Trainer"),
        (tclt, "Training Certified LM Trainer") 
        ])
    
    @staticmethod
    def get_role_list():
        return [WTMRoles.admin, WTMRoles.officer, WTMRoles.fc, WTMRoles.lm, WTMRoles.tbadge, WTMRoles.resident,
                WTMRoles.dev, WTMRoles.leadership,
                WTMRoles.mod_mail_resident, WTMRoles.mod_mail_tbadge,
                WTMRoles.ct, WTMRoles.clt, WTMRoles.af, WTMRoles.tct, WTMRoles.tclt
                ]
    
    @staticmethod
    def get_display_name(name):
        try:
            return WTMRoles.dnames[name]
        except KeyError:
            return name


DEFAULT_PREFIX = "default"
