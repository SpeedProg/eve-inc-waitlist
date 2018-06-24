from typing import Dict, Any


class NameItem(object):
    def __init__(self, data: Dict[str, Any]):
        self.__data: Dict[str, Any] = data

    @property
    def name(self):
        return self.__data['name']

    @property
    def id(self):
        return self.__data['id']

    @property
    def category(self):
        return self.__data['category']
