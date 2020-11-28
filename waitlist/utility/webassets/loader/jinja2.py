from jinja2 import nodes, exceptions
from webassets import Bundle
from webassets.loaders import GlobLoader, LoaderError
from webassets.ext.jinja2 import AssetsExtension


"""
Class originally from webassets jinja2 loader 
Will not build bundle when output is None 
"""
class Jinja2Loader(GlobLoader):
    """Parse all the Jinja2 templates in the given directory, try to
    find bundles in active use.

    Try all the given environments to parse the template, until we
    succeed.
    """

    def __init__(self, assets_env, directories, jinja2_envs, charset='utf8', jinja_ext='*.html'):
        self.asset_env = assets_env
        self.directories = directories
        self.jinja2_envs = jinja2_envs
        self.charset = charset
        self.jinja_ext = jinja_ext

    def load_bundles(self):
        bundles = []
        for template_dir in self.directories:
            for filename in self.glob_files((template_dir, self.jinja_ext)):
                bundles.extend(self.with_file(filename, self._parse) or [])
        return bundles

    def _parse(self, filename, contents):
        for _, env in enumerate(self.jinja2_envs):
            try:
                t = env.parse(contents.decode(self.charset))
            except exceptions.TemplateSyntaxError:
                pass
            else:
                result = []
                def _recurse_node(node_to_search):
                    for node in node_to_search.iter_child_nodes():
                        if isinstance(node, nodes.Call):
                            if (isinstance(node.node, nodes.ExtensionAttribute)
                               and node.node.identifier == AssetsExtension.identifier):
                                cfilter, output, _, depends, files = node.args
                                if output.as_const() is not None:
                                    bundle = Bundle(
                                        *AssetsExtension.resolve_contents(files.as_const(), self.asset_env),
                                        **{
                                            'output': output.as_const(),
                                            'depends': depends.as_const(),
                                            'filters': cfilter.as_const()})
                                    result.append(bundle)
                        else:
                            _recurse_node(node)
                for node in t.iter_child_nodes():
                    _recurse_node(node)
                return result
        else:
            raise LoaderError('Jinja parser failed on %s, tried %d environments' % (
                filename, len(self.jinja2_envs)))
        return False

