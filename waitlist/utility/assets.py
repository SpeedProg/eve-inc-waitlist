from webassets.bundle import Bundle
from flask_assets import Environment


def register_asset_bundles(assets: Environment):
    themes_dark = Bundle('css/themes/dark.css',
                         filters='cssmin',
                         output='gen/themes/dark.%(version)s.css')
    themes_darkpurple = Bundle('css/themes/dark_purple.css',
                               filters='cssmin',
                               output='gen/themes/dark_purple.%(version)s.css')
    themes_default = Bundle('css/themes/default.css',
                            filters='cssmin',
                            output='gen/themes/default.%(version)s.css')

    i18n_de = Bundle('local/de.json', filters="jsonmin",
                     output='gen/local/de.%(version)s.json')
    i18n_en = Bundle('local/en.json', filters="jsonmin",
                     output='gen/local/en.%(version)s.json')

    bundles = {
        'themes.dark': themes_dark,
        'themes.dark_purple': themes_darkpurple,
        'themes.default': themes_default,
        'i18n.de': i18n_de,
        'i18n.en': i18n_en,
    }
    assets.register(bundles)
