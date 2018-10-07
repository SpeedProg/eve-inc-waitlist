from typing import List, Union
from logging import _nameToLevel


class LogDedicatedLevelFilter(object):
    def __init__(self, levels: List[Union[int, str]]):
        self.__levels = []
        for level in levels:
            if isinstance(level, str):
                val = _nameToLevel.get(level)
                if val is not None:
                    self.__levels.append(val)

    def filter(self, log_record):
        return log_record.levelno in self.__levels
