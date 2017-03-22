from typing import Dict, Sequence

from flask_principal import RoleNeed, Permission, IdentityContext

from waitlist import db
from waitlist.storage.database import Permission as DBPermission, Role


class StaticRoles(object):
    ADMIN = 'admin'


class AddPermission(Permission):

    def add_role(self, name):
        self.needs.add(RoleNeed(name))

    def remove_role(self, name):
        for need in self.needs:
            if need.value == name:
                self.needs.remove(need)



class PermissionManager(object):

    def __init__(self) -> None:
        self.__permissions: Dict[str, AddPermission] = {}
        self.__definitions: Dict[str, bool] = {}
        self.__load_permissions()
    
    def __load_permissions(self) -> None:
        self.__permissions[StaticRoles.ADMIN] = AddPermission(RoleNeed(StaticRoles.ADMIN))
        permissions: Sequence[DBPermission] = db.session.query(DBPermission).all()
        for permission in permissions:
            perm = AddPermission()
            for role in permission.roles_needed:
                perm.addNeed(role.name)

            self.__add_permission(permission.name, perm)

    def __add_permission(self, name: str, perm: AddPermission) -> None:
        self.__permissions[name] = self.__permissions[StaticRoles.ADMIN].union(perm)

    def get_permission(self, name: str) -> Permission:
        if name in self.__definitions:
            if name in self.__permissions:
                return self.__permissions[name]
            else:
                return Permission(RoleNeed(StaticRoles.ADMIN))
        else:
            raise ValueError(f'Permission [{ name }] is not defined!')

    def get_permissions(self):
        return self.__permissions[:]
    
    def require(self, name: str) -> IdentityContext:
        if name in self.__permissions:
            return self.__permissions[name].require()
        return self.__permissions[StaticRoles.ADMIN].require()

    def define_permission(self, name: str) -> None:
        if name not in self.__definitions:
            self.__definitions[name] = True
            # if it is not in datebase add it
            if db.session.query(DBPermission).filter(DBPermission.name == name).first() == None:
                perm = DBPermission(name=name)
                db.session.add(perm)
                db.session.commit()

    def get_definitions(self) -> Dict[str, bool]:
        return self.__definitions

    def add_role_to_permission(self, perm_name, role_name):
        if not perm_name in self.__definitions:
            return

        perm: DBPermission = db.session.query(DBPermission).filter(DBPermission.name == perm_name).first()
        if perm is None:
            return
        has_role = False
        for role in perm.roles_needed:
            if role.name == role_name:
                has_role = True

        if not has_role:
            dbrole = db.session.query(Role).filter(Role.name == role_name).first()
            if dbrole is None:
                return
            perm.roles_needed.append(dbrole)
            # add it to our cache too
            self.__permissions[perm_name].add_role(dbrole.name)
            db.session.commit()

    def remove_role_from_permission(self, perm_name, role_name):
        if not perm_name in self.__definitions:
            return

        self.__permissions[perm_name].remove_role(role_name)
        # now remove from db
        dbrole = db.session.query(Role).filter(Role.name == role_name).first()
        if dbrole is None:
            return

        dbperm: DBPermission = db.session.query(DBPermission).filter(DBPermission.name == perm_name).first()
        if dbperm is None:
            return

        dbperm.roles_needed.remove(dbrole)
        db.session.commit()




