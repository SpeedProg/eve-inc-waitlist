__all__ = ['main_nav']

from .models import Navbar
from waitlist.utility.constants.menu import MAIN_NAV_IDENTITY
from waitlist.utility import config
from .config_loader import load_config_adds

main_nav = Navbar(MAIN_NAV_IDENTITY, 'mainNavbar', config.title)

load_config_adds(config.menu_adds, main_nav)
