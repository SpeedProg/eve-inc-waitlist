from .models import Navbar, Menu, MenuItem, DropdownMenu, DropdownItem, DropdownDivider
from waitlist.utility.constants.menu import MAIN_NAV_IDENTITY,\
    LEFT_MENU_IDENTITY, RIGHT_MENU_IDENTITY
from waitlist.utility import config
from .config_loader import load_config_adds

main_nav = Navbar(MAIN_NAV_IDENTITY, 'mainNavbar', config.title)

load_config_adds(config.menu_adds, main_nav)
