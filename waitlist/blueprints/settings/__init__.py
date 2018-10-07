from typing import Callable, Tuple, List

from waitlist import app
from flask_babel import lazy_gettext
from flask.helpers import url_for

__settings_menu: List[Tuple[str, str, Callable[[], bool]]] = []


def __get__menu_entry_key(entry: Tuple[str, str,  Callable[[], bool]]):
    return entry[1]


def add_menu_entry(url: str, name: str, permission_callable: Callable[[], bool]):
    __settings_menu.append((url, name, permission_callable))
    __settings_menu.sort(key=__get__menu_entry_key)


@app.context_processor
def inject_menu():
    return dict(settings_menu=__settings_menu)
