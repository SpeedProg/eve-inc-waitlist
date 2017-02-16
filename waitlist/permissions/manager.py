from flask_principal import RoleNeed, Permission


class StaticRoles(object):
    ADMIN = 'admin'


class PermissionManager(object):

    def __init__(self):
        self.__permissions = {}
        self.__definitions = {}
        self.__load_permissions()
    
    def __load_permissions(self):
        pass

    def __add_permission(self, name, perm):
        self.__permissions[name] = self.__permissions['admin'].union(perm)

    def get_permission(self, perm):
        if perm in self.__definitions:
            if perm in self.__permissions:
                return self.__permissions[perm]
            else:
                return Permission(RoleNeed(StaticRoles.ADMIN))
        else:
            raise ValueError(f'Permission [${ perm }] is not defined!')
    
    def require(self, perm):
        return self.__permissions[perm].require()

    def define_permission(self, name):
        self.__definitions[name] = True

    def get_definitions(self):
        return self.__definitions

