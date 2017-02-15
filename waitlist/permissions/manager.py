from flask_principal import RoleNeed, Permission
from waitlist.data.names import WTMRoles


class PermissionManager:
    def __init__(self):
        self.permissions = {}
        self.__load_permissions()
    
    def __load_permissions(self):
        self.permissions['admin'] = Permission(RoleNeed(WTMRoles.admin))
        self.__add_permission('dev', Permission(RoleNeed(WTMRoles.dev)))
        self.__add_permission('leadership', Permission(RoleNeed(WTMRoles.leadership)))
        self.__add_permission('officer', Permission(RoleNeed(WTMRoles.officer)))
        self.__add_permission('council', self.get_permission('leadership').union(self.get_permission('officer')))
        self.__add_permission('history_search', self.permissions['leadership'])
        self.__add_permission('inserts', Permission())
        self.__add_permission('trainee', Permission(RoleNeed(WTMRoles.tbadge), RoleNeed(WTMRoles.resident)))
        self.__add_permission('fullcommander', Permission(RoleNeed(WTMRoles.fc), RoleNeed(WTMRoles.lm)))
        self.__add_permission('commandcore', self.permissions['trainee'].union(self.permissions['fullcommander']))
        self.__add_permission('account_notes', self.permissions['officer'].union(self.permissions['leadership']))
        self.__add_permission('view_profile', self.get_permission('council'))
        self.__add_permission('add_notes', self.get_permission('council'))
        self.__add_permission('view_notes', self.get_permission('council').union(self.get_permission('add_notes')))
        self.__add_permission('send_mail', self.get_permission('council'))
        self.__add_permission('calendar_event_see_all', self.get_permission('council'))
        self.__add_permission('fleetview', self.get_permission('dev'))

    def __add_permission(self, name, perm):
        self.permissions[name] = self.permissions['admin'].union(perm)

    def get_permission(self, perm):
        return self.permissions[perm]
    
    def require(self, perm):
        return self.permissions[perm].require()
