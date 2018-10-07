from typing import Dict, Sequence

import logging
from flask_principal import RoleNeed, Permission, IdentityContext

from waitlist import db
from waitlist.storage.database import Permission as DBPermission, Role

logger = logging.getLogger(__name__)


class StaticRoles(object):
    ADMIN = 'admin'


class StaticPermissions(object):
    ADMIN = 'admin_tools'


class AddPermission(Permission):

    def __init__(self, *args):
        super(AddPermission, self).__init__(*args)

    def add_role(self, name):
        self.needs.add(RoleNeed(name))

    def has_role(self, name):
        rneed = RoleNeed(name)
        return rneed in self.needs

    def remove_role(self, name):
        role: RoleNeed = None
        for need in self.needs:
            if need.value == name:
                role = need
                break

        self.needs.remove(role)

    def union(self, other):
        """Create a new permission with the requirements of the union of this
        and other.

        :param other: The other permission
        """
        p = AddPermission(*self.needs.union(other.needs))
        p.excludes.update(self.excludes.union(other.excludes))
        return p


class PermissionManager(object):

    def __init__(self) -> None:
        self.__permissions: Dict[str, AddPermission] = {}
        self.__definitions: Dict[str, bool] = {}
        self.__load_permissions()
    
    def __load_permissions(self) -> None:
        # make sure admin role exists
        if not PermissionManager.role_exists(StaticRoles.ADMIN):
            r = Role(name=StaticRoles.ADMIN, displayName=StaticRoles.ADMIN)
            db.session.add(r)
            db.session.commit()

        # load admin perm first
        self.__permissions[StaticPermissions.ADMIN] = AddPermission()
        admin_perm: DBPermission = db.session.query(DBPermission).filter(
            DBPermission.name == StaticPermissions.ADMIN).first()
        if admin_perm is None:
            admin_perm: DBPermission = DBPermission(name=StaticPermissions.ADMIN)
            admin_role: Role = db.session.query(Role).filter(Role.name == StaticRoles.ADMIN).first()
            admin_perm.roles_needed.append(admin_role)
            db.session.add(admin_perm)
            db.session.commit()
        else:
            # make sure the admin role is in there
            has_admin_role = False
            for role_need in admin_perm.roles_needed:
                if role_need.name == StaticRoles.ADMIN:
                    has_admin_role = True
                    break
            if not has_admin_role:
                admin_role: Role = db.session.query(Role).filter(Role.name == StaticRoles.ADMIN).first()
                admin_perm.roles_needed.append(admin_role)
                db.session.commit()

        for role in admin_perm.roles_needed:
            self.__permissions[StaticPermissions.ADMIN].add_role(role.name)

        permissions: Sequence[DBPermission] = db.session.query(DBPermission)\
            .filter(DBPermission.name != StaticPermissions.ADMIN).all()
        for permission in permissions:
            perm = AddPermission()
            for role in permission.roles_needed:
                perm.add_role(role.name)

            self.__add_permission(permission.name, perm)

    def __add_permission(self, name: str, perm: AddPermission) -> None:
        self.__permissions[name] = self.__permissions[StaticPermissions.ADMIN].union(perm)

    def get_permission(self, name: str) -> AddPermission:
        if name in self.__definitions:
            if name not in self.__permissions:
                self.__add_permission(name, AddPermission(RoleNeed(StaticRoles.ADMIN)))

            return self.__permissions[name]
        else:
            raise ValueError(f'Permission [{ name }] is not defined!')

    @staticmethod
    def get_roles():
        return db.session.query(Role).all()

    @staticmethod
    def role_exists(name: str) -> bool:
        return db.session.query(Role).filter(Role.name == name).first() is not None

    @staticmethod
    def add_role(name: str, display_name: str) -> None:
        # lets check if this role exists
        if PermissionManager.role_exists(name):
            return

        role = Role(name=name, displayName=display_name)
        db.session.add(role)
        db.session.commit()

    def get_permissions(self) -> Dict[str, AddPermission]:
        return self.__permissions

    def require(self, name: str) -> IdentityContext:
        if name in self.__permissions:
            return self.__permissions[name].require()
        return self.__permissions[StaticPermissions.ADMIN].require()

    def define_permission(self, name: str) -> None:
        if name not in self.__definitions:
            self.__definitions[name] = True
            # if it is not in datebase add it
            if db.session.query(DBPermission).filter(DBPermission.name == name).first() is None:
                perm = DBPermission(name=name)
                db.session.add(perm)
                db.session.commit()

    def get_definitions(self) -> Dict[str, bool]:
        return self.__definitions

    def add_role_to_permission(self, perm_name: str, role_name: str) -> None:
        if perm_name not in self.__definitions:
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
            # the admin permission was unioned with all other permissions, if it changes we need to reload them all
            if perm_name == StaticPermissions.ADMIN:
                self.__permissions: Dict[str, AddPermission] = {}
                self.__load_permissions()

    def remove_role_from_permission(self, perm_name: str, role_name: str) -> None:
        if perm_name not in self.__definitions:
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

        # the admin permission was unioned with all other permissions, if it changes we need to reload them all
        if perm_name == StaticPermissions.ADMIN:
            self.__permissions: Dict[str, AddPermission] = {}
            self.__load_permissions()
