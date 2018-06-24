from flask.templating import render_template

main_menu_items = []


class MainMenuItem:
    def __init__(self, text, classes, url, order=None):
        self.text = text
        self.classes = classes
        self.url = url
        self.template = 'mainmenu/menuitem.html'
        self.order = order if order is not None else 9999

    def render(self):
        return render_template(self.template,
                               item=self)


def register_menu_item(item: MainMenuItem) -> None:
    main_menu_items.append(item)
