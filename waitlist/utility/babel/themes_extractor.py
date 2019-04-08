import json
def extract(fileobj, keywords, comment_tags, options):
    """Babel extraction method for theme names
    """

    # this should be an array of objects {"name" : "Theme Name"}
    theme_settings = json.load(fileobj);
    for theme_obj in theme_settings:
        # we need to yield lineno, message, comments
        yield 0, "", theme_obj['name'], list()

