from flask.templating import render_template, render_template_string
import logging
from waitlist import permissions
from typing import List, Optional, Dict, Union, Any
from flask_babel import lazy_gettext
from flask_login.utils import current_user


logger = logging.getLogger(__name__)


class OrderedItem(object):
    def __init__(self, order=None):
        self.order = 9999 if order is None else int(order)

    @staticmethod
    def sort_key(item) -> int:
        return item.order


class MenuItem(OrderedItem):
    def __init__(self, title, classes, url, iconclass=None, order=None,
                 url_for=False, perms=None, customtemplate=None,
                 use_gettext=True,
                 need_authenticated: bool=False):
        super(MenuItem, self).__init__(order)
        if use_gettext:
            self.title = lazy_gettext(title)
        else:
            self.title = title
        self.classes = classes
        self.url = url
        self.iconclass = iconclass
        self.template = 'mainmenu/item.html'
        self.url_for = url_for
        self.perms = [] if perms is None else perms
        self.customtemplate = customtemplate
        self.need_authenticated = need_authenticated

    def render(self):
        for perm_name in self.perms:
            if not permissions.perm_manager.get_permission(perm_name).can():
                return ''

        if self.need_authenticated and not current_user.is_authenticated:
            return ''

        customhtml = None
        if self.customtemplate:
            customhtml = render_template_string(self.customtemplate, item=self)

        return render_template(self.template,
                               item=self, customhtml=customhtml)

    def __repr__(self):
        return f'<MenuItem order={self.order} text={self.title}>'


class Menu(OrderedItem):
    def __init__(self, identity: str, classes: str='justify-content-start',
                 order: int=None, perms: List[str]=None,
                 need_authenticated: bool=False):
        super(Menu, self).__init__(order)
        self.items = []
        self.identity = identity
        self.perms = [] if perms is None else perms
        self.classes = classes
        self.__submenuregistry = dict()
        self.__delayed_item_adds = dict()
        self.__delayed_menu_adds = dict()
        self.template = 'mainmenu/menu.html'
        self.need_authenticated = need_authenticated

    def add_item(self, item: MenuItem, target_id: str=None):
        if target_id is None:
            target_id = self.identity

        logger.debug('Registering %r under %s', item, target_id)
        target = self.__get_menu_by_identity(target_id)

        # target menu is not know yet
        if target is None:
            self.__add_delayed(item, target_id, self.__delayed_item_adds)
            return

        if target is self:
            self.items.append(item)
            self.items.sort(key=OrderedItem.sort_key, reverse=False)
        else:
            target.add_item(item, target_id)

    def add_submenu(self, menu, target_id: str=None):
        if target_id is None:
            target_id = self.identity

        logger.debug('Registering %r under %s', menu, target_id)
        target = self.__get_menu_by_identity(target_id)

        # lets check if we have delayed adds for this menu
        self.__handle_delayed_adds(menu)

        # if the target is not know (yet?)
        # save it for delayed adding
        if target is None:
            logger.debug('Target is None delaying %r', menu)
            self.__add_delayed(menu, target_id, self.__delayed_menu_adds)
            self.__submenuregistry[menu.identity] = menu
            return

        # if it is us add it
        if target is self:
            logger.debug('Adding as submenu to %r', self),
            self.items.append(menu)
            self.items.sort(key=OrderedItem.sort_key, reverse=False)
        else:
            logger.debug('Calling %r for add', target)
            target.add_submenu(menu, target_id)

        self.__submenuregistry[menu.identity] = menu

    def __get_menu_by_identity(self, identity: str):
        if self.identity == identity:
            return self
        if identity in self.__submenuregistry:
            return self.__submenuregistry[identity]

        logger.debug('Failed to get menu for identity=%s returning None',
                     identity)

        return None

    def __add_delayed(self, item: Union[MenuItem, Any],
                      target_id: str, queue: Dict[str, Any]):
            if target_id in queue:
                queue[target_id].append(item)

            else:
                queue[target_id] = [item]

            return

    def __handle_delayed_adds(self, menu):
                # check for menus first
        if menu.identity in self.__delayed_menu_adds:
            for delayed_menu in self.__delayed_menu_adds[menu.identity]:
                menu.add_submenu(delayed_menu)

        # now check for item adds
        for menu.identity in self.__delayed_item_adds:
            for delayed_item in self.__delayed_item_adds[menu.identity]:
                menu.add_item(delayed_item)

    def render(self):
        for perm_name in self.perms:
            if not permissions.perm_manager.get_permission(perm_name).can():
                return ''

        if self.need_authenticated and not current_user.is_authenticated:
            return ''

        return render_template(self.template,
                               menu=self)

    def __repr__(self):
        return f'<Menu identity={self.identity} order={self.order}>'


class Navbar(Menu):
    def __init__(self, identity: str, htmlid: str, brand: str=None,
                 need_authenticated: bool=False):
        super(Navbar, self).__init__(identity, need_authenticated)
        self.htmlid = htmlid
        self.brand = brand
        self.template = 'mainmenu/navbar.html'

    def __repr__(self):
        return (f'<Navbar identity={self.identity} order={self.order} '
                f'htmlid={self.htmlid}>')


class DropdownMenu(Menu):
    def __init__(self, identity, title: str='', classes: str='',
                 iconclass: Optional[str]=None, order: Optional[int]=None,
                 perms: List[str]=None, customtemplate: Optional[str]=None,
                 nodetag: str='a', dropclasses: str='',
                 triggerclasses: str='nav-link', use_gettext=True,
                 need_authenticated: bool=False
                 ):
        super(DropdownMenu, self).__init__(identity, classes, order, perms,
                                           need_authenticated)
        self.iconclass = iconclass
        if use_gettext:
            self.title = lazy_gettext(title)
        else:
            self.title = title
        self.classes = classes
        self.customtemplate = customtemplate
        self.nodetag = nodetag
        self.dropclasses = dropclasses
        self.triggerclasses = triggerclasses
        self.template = 'mainmenu/dropdown.html'

    def render(self):
        for perm_name in self.perms:
            if not permissions.perm_manager.get_permission(perm_name).can():
                return
        customhtml = None

        if self.customtemplate is not None:
            customhtml = render_template_string(self.customtemplate, menu=self)

        return render_template(self.template,
                               menu=self, customhtml=customhtml)


class DropdownDivider(MenuItem):
    def __init__(self, order=None, perms=None,
                 need_authenticated: bool=False):
        super(DropdownDivider, self).__init__(None, None, None, order=order,
                                              perms=perms, need_authenticated=need_authenticated)

    def render(self):
        for perm_name in self.perms:
            if not permissions.perm_manager.get_permission(perm_name).can():
                return ''

        if self.need_authenticated and not current_user.is_authenticated:
            return ''

        return '<div class="dropdown-divider"></div>'


class DropdownItem(MenuItem):
    def __init__(self, title, classes, url, iconclass=None, order=None,
                 url_for=False, perms=None, customtemplate=None,
                 use_gettext=True,
                 need_authenticated: bool=False
                 ):
        super(DropdownItem, self).__init__(title, classes, url, iconclass,
                                           order, url_for, perms,
                                           customtemplate, use_gettext,
                                           need_authenticated
                                           )
        self.template = 'mainmenu/dropdownitem.html'
