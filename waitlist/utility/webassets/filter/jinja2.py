from webassets.filter import Filter
from webassets.utils import hash_func

class CacheableJinja2Context():
    def __init__(self, context = {}):
        self.context = context

    def unique(self):
        return self.context

    def context(self):
        return self.context


class CacheableJinja2Filter(Filter):
    name = 'cacheablejinja2'
    max_debug_level = None

    def __init__(self, context: CacheableJinja2Context, jinja_env):
        super(CacheableJinja2Filter, self).__init__()
        self.context = context or CacheableJinja2Context()
        self.jinja_env = jinja_env

    def id(self):
        return hash_func((self.name, self.unique(),))

    def unique(self):
        return self.context.unique()

    def input(self, _in, out, source_path, output_path, **kw):
        out.write(self.jinja_env.from_string(_in.read()).render(self.context.context()))

