from flask_babel import lazy_gettext

SHIP_CHECK_TYPEID = 1
SHIP_CHECK_INVGROUP = 2
SHIP_CHECK_MARKETGROUP = 3
MODULE_CHECK_TYPEID = 4
MODULE_CHECK_MARKETGROUP = 5

CHECK_NAME_MAP = {
    SHIP_CHECK_TYPEID: lazy_gettext('Hull by TypeId'),
    SHIP_CHECK_INVGROUP: lazy_gettext('Hull by Inventory Group'),
    SHIP_CHECK_MARKETGROUP: lazy_gettext('Hull by Market Group'),
    MODULE_CHECK_TYPEID: lazy_gettext('Module by TypeId'),
    MODULE_CHECK_MARKETGROUP: lazy_gettext('Module by Market Group')
}

