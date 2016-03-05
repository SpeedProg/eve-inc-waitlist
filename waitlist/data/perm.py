from flask_principal import Permission, RoleNeed
from waitlist.data.names import WTMRoles


perm_settings = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm),
                             RoleNeed(WTMRoles.resident))

perm_admin = Permission(RoleNeed(WTMRoles.admin))

perm_management = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm))

perm_remove_player = Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.tbadge),
                             RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.lm))

perm_officer = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.officer))