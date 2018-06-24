from waitlist.utility.mainmenu.hooks import MainMenuItem, register_menu_item
from flask_babel import lazy_gettext
from flask.helpers import url_for
from flask.templating import render_template


class XupMenuItem(MainMenuItem):
    def __init__(self, classes, url, order=None):
        super(XupMenuItem, self).__init__(lazy_gettext('X-UP'), classes,
                                              url, order)
        self.template = 'xup/mainmenuitem.html'

    def render(self):
        return render_template(self.template,
                               item=self)


def register():
    register_menu_item(XupMenuItem('', 'xup.index'))
