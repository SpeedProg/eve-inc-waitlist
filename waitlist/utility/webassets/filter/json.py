from webassets.filter import Filter
import json


class JsonMinFilter(Filter):
    name = 'jsonmin'

    def output(self, _in, out, **kwargs):
        out.write(_in.read())

    def input(self, _in, out, **kwargs):
        json.dump(json.load(_in), out,
                  separators=(',', ':'))
