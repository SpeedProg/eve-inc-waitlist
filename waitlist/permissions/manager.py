from flask_principal import RoleNeed, Permission
from waitlist.data.names import WTMRoles
class PermissionManager():
    def __init__(self):
        self.permissions = {}
        self.__loadPermissions()
    
    def __loadPermissions(self):
        self.permissions['history_search'] = Permission(RoleNeed(WTMRoles.admin), RoleNeed(WTMRoles.leadership))
        self.permissions['inserts'] = Permission(RoleNeed(WTMRoles.admin))
    
    def getPermission(self, perm):
        return self.permissions[perm]
    
    def require(self, perm):
        return self.permissions[perm].require()
