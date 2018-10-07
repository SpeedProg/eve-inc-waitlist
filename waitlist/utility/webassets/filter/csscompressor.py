from webassets.filter import Filter


class CompressorMinFilter(Filter):
    """Minifies CSS with compressor.

    Requires the ``csscompressor`` package
    (https://github.com/sprymix/csscompressor),
    which is a port of the YUI CSS compression algorithm.
    """

    name = 'csscomp'

    def setup(self):
        try:
            import csscompressor
        except ImportError:
            raise EnvironmentError('The "compressor" package is not installed')
        else:
            self.comp = csscompressor

    def output(self, _in, out, **kwargs):
        out.write(self.comp.compress(_in.read()))
