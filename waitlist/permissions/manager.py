from typing import Dict

from flask_principal import RoleNeed, Permission, IdentityContext


class StaticRoles(object):
    ADMIN = 'admin'


class PermissionManager(object):

    def __init__(self) -> None:
        self.__permissions: Dict[str, Permission] = {}
        self.__definitions: Dict[str, bool] = {}
        self.__load_permissions()
    
    def __load_permissions(self) -> None:
        self.__permissions[StaticRoles.ADMIN] = Permission(RoleNeed(StaticRoles.ADMIN))
        pass

    def __add_permission(self, name: str, perm: Permission) -> None:
        self.__permissions[name] = self.__permissions[StaticRoles.ADMIN].union(perm)

    def get_permission(self, name: str) -> Permission:
        if name in self.__definitions:
            if name in self.__permissions:
                return self.__permissions[name]
            else:
                return Permission(RoleNeed(StaticRoles.ADMIN))
        else:
            raise ValueError(f'Permission [{ name }] is not defined!')
    
    def require(self, name: str) -> IdentityContext:
        if name in self.__permissions:
            return self.__permissions[name].require()
        return self.__permissions[StaticRoles.ADMIN].require()

    def define_permission(self, name: str) -> None:
        if name not in self.__definitions:
            self.__definitions[name] = True
            print(name)

    def get_definitions(self) -> Dict[str, bool]:
        return self.__definitions

