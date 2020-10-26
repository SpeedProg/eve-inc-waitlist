import json
from os import path
import shutil
from webassets.utils import hash_func
from waitlist.utility.webassets.loader.jinja2 import Jinja2Loader
from waitlist.utility.webassets.filter.jinja2 import CacheableJinja2Filter
from flask_assets import Environment


def register_asset_bundles(assets: Environment):
    ThemeBundle(assets)
    
    translations = []
    for locale in assets.app.babel_instance.list_translations():
        LocaleJinja2Bundle(
            assets,
            path.join(assets.app.static_folder, 'local', locale.language + '.json'),
        )
        translations.append((locale.language, locale.get_language_name()))

    assets.app.jinja_env.globals.update(translations=translations)

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


class LocaleJinja2Bundle():

    def __init__(self, assets: Environment, locale_path):
        self.path = locale_path
        self.lang_code = path.basename(locale_path).replace('.json', '')
        assets.register(
            self.lang_code,
            'js/i18n.js',
            filters=(
                CacheableJinja2Filter(self, assets.app.jinja_env),
                'babili',
            ),
            output='gen/js/i18n.' + self.lang_code + '.%(version)s.js',
        )

    def unique(self):
        return {
            'lang_code': self.lang_code,
            'lang_mtime': '{}'.format(path.getmtime(self.path)),
        }

    def context(self):
        return {
            'lang_code': self.lang_code,
            'lang_json': json.dumps(self.validate(), separators=(',', ':'), ensure_ascii=False),
        }

    def validate(self):
        with open(self.path, 'r', encoding='utf-8') as fp:
            lang = json.load(fp)
            if not ('@metadata' in lang and 'locale' in lang['@metadata']):
                raise Exception('unable to validate {} as locale file for {}'.format(self.path, self.lang_code))
            return lang


class ThemeBundle():

    def __init__(self, assets: Environment):
        themes_config_filename = './config/themes.json'
        if not path.isfile(themes_config_filename):
            if path.exists('./config/themes.example.json') and path.isfile('./config/themes.example.json'):
                shutil.copyfile('./config/themes.example.json', themes_config_filename)

        if path.exists(themes_config_filename):
            with open(themes_config_filename, 'r') as fp:
                self.config = json.load(fp)
            assets.app.jinja_env.globals.update(themes=self.config)
        else:
            self.config = {}

        self.assets = assets
        self.hash = hash_func(self.config)

        for theme in self.config:
            if 'paths' in theme:
                self.assets.register(
                    'theme_' + theme['id'],
                    *theme['paths'],
                    filters='csscomp',
                    output='gen/themes/' + theme['id'] + '.%(version)s.css',
                )

        self.assets.register(
            'themes.js',
            ['static/js/themes.js'],
            filters=(
                CacheableJinja2Filter(self, assets.app.jinja_env),
                'babili',
            ),
            output='gen/themes.%(version)s.js',
        )

    def unique(self):
        hashset = [self.hash]
        for theme in self.config:
            if theme['paths']:
                hashset.append(self.assets['theme_' + theme['id']].urls())
        return hashset

    def context(self):
        return {}

