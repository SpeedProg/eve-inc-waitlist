from flask_principal import Permission, RoleNeed
from waitlist.data.names import WTMRoles


perm_settings = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm),
                             RoleNeed(WTMRoles.resident), RoleNeed(WTMRoles.officer), RoleNeed(WTMRoles.dev), RoleNeed(WTMRoles.leadership))

perm_admin = Permission(RoleNeed(WTMRoles.admin))
perm_accounts = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.leadership), RoleNeed(WTMRoles.dev))

perm_management = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm), RoleNeed(WTMRoles.officer), RoleNeed(WTMRoles.leadership))

perm_officer = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.officer))

perm_feedback = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.officer), RoleNeed(WTMRoles.dev), RoleNeed(WTMRoles.leadership))

perm_dev = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.dev))

perm_leadership = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.leadership))

perm_fleetlocation = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.officer), RoleNeed(WTMRoles.leadership))

perm_bans = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.leadership), RoleNeed(WTMRoles.officer))

perm_viewfits = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.leadership), RoleNeed(WTMRoles.officer),
                            RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.lm), RoleNeed(WTMRoles.tbadge), RoleNeed(WTMRoles.resident))
perm_comphistory = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.lm))