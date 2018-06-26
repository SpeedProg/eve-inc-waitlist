# handle config menus
from typing import Any, Optional, Tuple, List
from waitlist.utility.constants.menu import MAIN_NAV_IDENTITY
from .models import Menu, DropdownDivider, DropdownItem, DropdownMenu, MenuItem
import logging
from flask_babel import gettext


logger = logging.getLogger(__name__)


def is_menuitem_section(name: str):
    return name.startswith('menu::menuitem::')


def is_dropdownmenu_section(name: str):
    return name.startswith('menu::ddmenu::')


def is_dropdownitem_section(name: str):
    return name.startswith('menu::dditem::')


def is_dropdowndivider_section(name: str):
    return name.startswith('menu::dddivider::')


def is_menu_section(name: str):
    return name.startswith('menu::menu::')


def get(name: str, section, default: Any=None):
    return section[name] if name in section else default


def get_perms(name: str, section):
    perms = get(name, section, '')  # perms need to be seperated by |
    if perms == '':
        perms = []
    else:
        perms = perms.split('|')
    return perms


def get_target_id_from_section(section):
    return get('target_id', section, MAIN_NAV_IDENTITY)


def get_menu(section_name: str, section: Any) -> Optional[Menu]:
    identity: str = get('identity', section, None)
    classes: str = get('classes', section, 'justify-content-start')
    order = get('order', section, None)
    perms = get_perms('perms', section)
    need_authenticated = get('need_authenticated', section, 'False').lower() == 'true'

    if identity is None:
        logger.error('Menu %s is missing required identity', section_name)
    return Menu(identity, classes, order, perms, need_authenticated)


def get_dropdowndivider(section):
    order = get('order', section, None)
    perms = get_perms('perms', section)
    need_authenticated = get('need_authenticated', section, 'False').lower() == 'true'
    return DropdownDivider(order, perms, need_authenticated)


def get_dropdownitem_from_section(section_name, section):
    title = get('title', section, None)
    use_gettext = get('use_gettext', section, 'False').lower() == 'true'
    classes = get('classes', section, '')
    url = get('url', section, None)
    iconclass = get('iconclass', section, '')
    order = get('order', section, None)
    url_for = get('url_for', section, 'False').lower() == 'true'
    perms = get_perms('perms', section)
    customtemplate = get('customtemplate', section, None)
    need_authenticated = get('need_authenticated', section, 'False').lower() == 'true'

    if (title is None or url is None) and customtemplate is None:
        logger.error('DropdownMenuItem %s is missing required title or url',
                     section_name)
        return None

    return DropdownItem(title, classes, url, iconclass,
                        order, url_for, perms,
                        customtemplate,
                        use_gettext, need_authenticated
                        )


def get_dropdownmenu_from_section(section_name, section):
    identity = get('identity', section, None)
    title = get('title', section, None)
    use_gettext = get('use_gettext', section, "False").lower() == "true"
    classes = get('classes', section, None)
    iconclass = get('iconclass', section, None)
    order = get('order', section, None)
    perms = get_perms('perms', section)
    customtemplate = get('customtemplate', section, None)
    nodetag = get('nodetag', section, 'a')
    dropclasses = get('dropclasses', section, '')
    triggerclasses = get('triggerclasses', section, 'nav-link')
    need_authenticated = get('need_authenticated', section, 'False').lower() == 'true'

    if title is None and customtemplate is None:
        logger.error('DropdownMenu %s is missing a title or customtemplate',
                     section_name)
        return None

    return DropdownMenu(identity, title, classes, iconclass, order, perms,
                        customtemplate, nodetag, dropclasses, triggerclasses,
                        use_gettext, need_authenticated)


def get_menuitem_from_section(section_name, section):
    title = get('title', section)
    use_gettext = get('use_gettext', section, 'False').lower() == 'true'
    classes = get('classes', section, '')
    url = get('url', section, None)
    url_for = get('url_for', section, 'False').lower() == 'true'
    iconclass = get('iconclass', section, '')
    order = get('order', section, None)
    perms = get_perms('perms', section)
    customtemplate = get('customtemplate', section, None)
    need_authenticated = get('need_authenticated', section, 'False').lower() == 'true'

    if url is None and customtemplate is None:
        logger.error('MenuItem %s is missing url or customtemplate',
                     section_name)
        return None

    if title is None and customtemplate is None:
        logger.error('MenuItem %s is missing a title or customtemplate',
                     section_name)
        return None

    return MenuItem(title, classes, url, iconclass=iconclass,
                    order=order, url_for=url_for, perms=perms,
                    customtemplate=customtemplate,
                    use_gettext=use_gettext,
                    need_authenticated=need_authenticated
                    )


def load_config_adds(menu_adds: List[Tuple[str, Any]], base_menu: MenuItem):
    logger.debug('We have %d config menu entries', len(menu_adds))
    for add in menu_adds:
        target_id = get_target_id_from_section(add[1])
        if is_menuitem_section(add[0]):
            menu_item = get_menuitem_from_section(add[0], add[1])
            if menu_item is not None:
                base_menu.add_item(menu_item, target_id)
        elif is_dropdownmenu_section(add[0]):
            menu = get_dropdownmenu_from_section(add[0], add[1])
            if menu is not None:
                base_menu.add_submenu(menu, target_id)
        elif is_dropdownitem_section(add[0]):
            item = get_dropdownitem_from_section(add[0], add[1])
            if item is not None:
                base_menu.add_item(item, target_id)
        elif is_dropdowndivider_section(add[0]):
            divider = get_dropdowndivider(add[1])
            base_menu.add_item(divider, target_id)
        elif is_menu_section(add[0]):
            menu = get_menu(add[0], add[1])
            if menu is not None:
                base_menu.add_submenu(menu, target_id)
        else:
            logger.error('Unknown menu section type %s', add[0])


# bunch of strings for getting picked up by translations
gettext('Help')
gettext('Tools')
gettext('Logout')
gettext('About')
gettext('Command Core List')
gettext('Comp History Search')
gettext('Custom Notifications')
gettext('Settings')
gettext('X-UP'),
gettext('Comp History')
gettext('Reform')
gettext('Not loggedin')
