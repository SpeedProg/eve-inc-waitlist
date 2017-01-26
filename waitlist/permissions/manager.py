from flask_principal import RoleNeed, Permission
from waitlist.data.names import WTMRoles
class PermissionManager():
    def __init__(self):
        self.permissions = {}
        self.__loadPermissions()
    
    def __loadPermissions(self):
        self.permissions['admin'] = Permission(RoleNeed(WTMRoles.admin))
        self.__addPermission('leadership', Permission(RoleNeed(WTMRoles.leadership)))
        self.__addPermission('officer', Permission(RoleNeed(WTMRoles.officer)))
        self.__addPermission('council', self.getPermission('leadership').union(self.getPermission('officer')))
        self.__addPermission('history_search', self.permissions['leadership'])
        self.__addPermission('inserts', Permission())
        self.__addPermission('trainee', Permission(RoleNeed(WTMRoles.tbadge), RoleNeed(WTMRoles.resident)))
        self.__addPermission('fullcommander', Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.lm)))
        self.__addPermission('commandcore', self.permissions['trainee'].union(self.permissions['fullcommander']))
        self.__addPermission('account_notes', self.permissions['officer'].union(self.permissions['leadership']))
        self.__addPermission('view_profile', self.getPermission('council'))
        self.__addPermission('add_notes', self.getPermission('council'))
        self.__addPermission('view_notes', self.getPermission('council').union(self.getPermission('add_notes')))
        self.__addPermission('send_mail', self.getPermission('council'))

    def __addPermission(self, name, perm):
        self.permissions[name] = self.permissions['admin'].union(perm)

    def getPermission(self, perm):
        return self.permissions[perm]
    
    def require(self, perm):
        return self.permissions[perm].require()
