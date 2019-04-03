from os import path
from webassets.bundle import Bundle
from waitlist.utility.webassets.loader.jinja2 import Jinja2Loader
from flask_assets import Environment


def register_asset_bundles(assets: Environment):
    themes_dark = Bundle('css/themes/dark.css',
                         filters='csscomp',
                         output='gen/themes/dark.%(version)s.css')
    themes_darkpurple = Bundle('css/themes/dark_purple.css',
                               filters='csscomp',
                               output='gen/themes/dark_purple.%(version)s.css')
    themes_default = Bundle('css/themes/default.css',
                            filters='csscomp',
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

    # bundles in templates should be preparsed when not auto building bundles
    if not assets.auto_build:

        # get the template directories of app and blueprints
        template_dirs = [path.join(assets.app.root_path, assets.app.template_folder)]
        template_dirs.extend(
           path.join(blueprint.root_path, blueprint.template_folder)
           for blueprint in assets.app.blueprints.values()
           if blueprint.template_folder is not None
        )

        # load bundles from templates
        bundles = Jinja2Loader(assets, template_dirs, [assets.app.jinja_env])\
            .load_bundles()

        # register bundles with asset environment
        assets.add(*[bundle for bundle in bundles if not bundle.is_container])
