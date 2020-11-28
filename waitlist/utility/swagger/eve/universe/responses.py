from waitlist.utility.swagger.eve import ESIResponse, get_expire_time,\
    get_error_msg_from_response
from typing import Any, ClassVar, List, Dict
from waitlist.utility.swagger.eve.universe.models import NameItem


class ResolveIdsResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in ResolveIdsResponse.okay_codes:
            super(ResolveIdsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.__data: Dict[int, NameItem] = set()
            self.__set_data(response.data)
        else:
            error_msg = get_error_msg_from_response(response)
            super(ResolveIdsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)

    def __set_data(self, data: List[Dict[str, Any]]):
        for item in data:
            self.__data[item.id] = NameItem(item)

    @property
    def data(self) -> Dict[int, NameItem]:
        """
        Get the requests data
        :returns dict of it to item info mapping,
         item info contains: id, name, category
        """
        return self.__data


class CategoriesResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in CategoriesResponse.okay_codes:
            super(CategoriesResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.__ids = response.data
        else:
            error_msg = get_error_msg_from_response(response)
            super(CategoriesResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)

    @property
    def data(self) -> List[int]:
        """
        Get the list of category ids
        :returns list of category ids
        """
        return self.__ids


class CategoryResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in CategoryResponse.okay_codes:
            super(CategoryResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.id = response.data['category_id']
            self.groups = response.data['groups']
            self.name = response.data['name']
            self.published = response.data['published']
        else:
            error_msg = get_error_msg_from_response(response)
            super(CategoryResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)


class GroupsResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in GroupsResponse.okay_codes:
            super(GroupsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.__ids = response.data
        else:
            error_msg = get_error_msg_from_response(response)
            super(GroupsResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)

    @property
    def data(self) -> List[int]:
        """
        Get the list of category ids
        :returns list of category ids
        """
        return self.__ids


class GroupResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in GroupResponse.okay_codes:
            super(GroupResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.category_id = response.data['category_id']
            self.id = response.data['group_id']
            self.name = response.data['name']
            self.published = response.data['published']
            self.types = response.data['types']
        else:
            error_msg = get_error_msg_from_response(response)
            super(GroupResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)


class TypesResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in TypesResponse.okay_codes:
            super(TypesResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.__ids = response.data
        else:
            error_msg = get_error_msg_from_response(response)
            super(TypesResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)

    @property
    def data(self) -> List[int]:
        """
        Get the list of category ids
        :returns list of category ids
        """
        return self.__ids


class TypeResponse(ESIResponse):
    okay_codes: ClassVar[List[int]] = [200]

    def __init__(self, response: Any) -> None:
        if response.status in TypeResponse.okay_codes:
            super(TypeResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, None)
            self.description = response.data['description']
            self.group_id = response.data['group_id']
            self.name = response.data['name']
            self.type_id = response.data['type_id']
            if 'market_group_id' in response.data:
                self.market_group_id = response.data['market_group_id']
            else:
                self.market_group_id = None

            if 'dogma_attributes' in response.data:
                self.dogma_attributes = response.data['dogma_attributes']
            else:
                self.dogma_attributes = None
            if 'dogma_effects' in response.data:
                self.dogma_effects = response.data['dogma_effects']
            else:
                self.dogma_effects = None
        else:
            error_msg = get_error_msg_from_response(response)
            super(TypeResponse,
                  self).__init__(get_expire_time(response),
                                 response.status, error_msg)
