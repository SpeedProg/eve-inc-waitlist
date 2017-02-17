from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager

add_menu_entry('calendar_settings.get_index', 'Events', perm_manager.get_permission('commandcore').can)
