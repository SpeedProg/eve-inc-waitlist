from webassets.filter import ExternalTool
from waitlist.utility import config


class BabiliFilter(ExternalTool):
    name = 'babili'

    options = {
        'binary': 'BABEL_BIN',
        'presets': 'BABEL_PRESETS',
        'extra_args': 'BABEL_EXTRA_ARGS',
        'run_in_debug': 'BABEL_RUN_IN_DEBUG',
    }

    def setup(self):
        super(BabiliFilter, self).setup()

    def output(self, _in, out, **kw):
        # node not configured
        if config.node_bin == '':
            out.write(_in.read())
            return

        # prepare arguments
        if self.presets:
            self.presets += ",minify"
        else:
            self.presets = "minify"
        if self.extra_args:
            self.extra_args.extend(['--no-babelrc', '--no-comments',])# '--plugins=transform-remove-console'])
        else:
            self.extra_args = ['--no-babelrc', '--no-comments']#, '--plugins=transform-remove-console']

        args = [config.node_bin + 'babel']
        if self.presets:
            args += ['--presets', self.presets]
        if self.extra_args:
            args.extend(self.extra_args)
        return self.subprocess(args, out, _in)
