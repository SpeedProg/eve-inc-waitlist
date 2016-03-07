from flask_principal import Permission, RoleNeed
from waitlist.data.names import WTMRoles


perm_settings = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm),
                             RoleNeed(WTMRoles.resident), RoleNeed(WTMRoles.officer), RoleNeed(WTMRoles.dev))

perm_admin = Permission(RoleNeed(WTMRoles.admin))
perm_accounts = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.officer))

perm_management = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm), RoleNeed(WTMRoles.officer))

perm_remove_player = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm), RoleNeed(WTMRoles.officer))

perm_officer = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.officer))

perm_feedback = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.officer), RoleNeed(WTMRoles.dev))