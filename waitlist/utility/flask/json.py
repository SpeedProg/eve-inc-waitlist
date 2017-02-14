# set json encoder so use less space in minified format
from flask.json import JSONEncoder


class MiniJSONEncoder(JSONEncoder):
    """Minify JSON output."""
    item_separator = ','
    key_separator = ':'
