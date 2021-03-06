from webassets.filter import ExternalTool
from waitlist.utility import config


class CSSOptimizerFilter(ExternalTool):
    name = 'csscomp'

    def setup(self):
        super(CSSOptimizerFilter, self).setup()

    def output(self, _in, out, **kw):
        # prepare arguments
        if config.node_bin == '':
            out.write(_in.read())
            return

        args = [config.node_bin + 'csso']

        return self.subprocess(args, out, _in)
