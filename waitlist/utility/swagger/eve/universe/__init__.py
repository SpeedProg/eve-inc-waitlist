from esipy.client import EsiClient
from waitlist.utility.swagger.eve import get_esi_client
from waitlist.utility.swagger import get_api
from waitlist.utility.swagger.eve.universe.responses import ResolveIdsResponse,\
    CategoriesResponse, CategoryResponse, GroupResponse, GroupsResponse,\
    TypesResponse, TypeResponse
from typing import List
from esipy.exceptions import APIException


class UniverseEndpoint(object):
    def __init__(self, client: EsiClient = None) -> None:
        if client is None:
            self.__client: EsiClient = get_esi_client(
                token=None, noauth=True, retry_request=True)
            self.__api: App = get_api()
        else:
            self.__client: EsiClient = client
            self.__api: App = get_api()

    def resolve_ids(self, ids_list: [int]) -> ResolveIdsResponse:
        """
        :param list maximum of 1000 ids allowed at once
        """
        resp = self.__client.request(
            self.__api.op['post_universe_names'](ids=ids_list))

        return ResolveIdsResponse(resp)

    def get_categories(self) -> CategoriesResponse:
        """
        Get response containing a list of all category ids
        """
        resp = self.__client.request(
            self.__api.op['get_universe_categories']())
        return CategoriesResponse(resp)

    def get_category(self, category_id: int) -> CategoryResponse:
        """
        Get response containing information about the category
        """
        resp = self.__client.request(
            self.__api.op['get_universe_categories_category_id'](
                category_id=category_id))
        return CategoryResponse(resp)

    def get_category_multi(self,
                           category_ids: List[int]) -> List[CategoryResponse]:
        ops = []
        for category_id in category_ids:
            ops.append(self.__api.op['get_universe_categories_category_id'](
                category_id=category_id))

        response_infos = self.__client.multi_request(ops)
        return [CategoryResponse(info[1]) for info in response_infos]

    def get_groups(self) -> List[GroupsResponse]:
        """
        Get response containing a list of all group ids
        """
        resp = self.__client.head(
            self.__api.op['get_universe_groups'](page=1))
        if (resp.status != 200):
            raise APIException("", resp.status)

        pages = 1
        if 'X-Pages' in resp.header:
            pages = int(resp.header['X-Pages'][0])

        ops = []
        for page in range(1, pages+1):
            ops.append(self.__api.op['get_universe_groups'](page=page))

        responses = self.__client.multi_request(ops)

        response_list: List[GroupsResponse] = []
        for data_tuple in responses:  # (request, response)
            response_list.append(GroupsResponse(data_tuple[1]))

        return response_list

    def get_group(self, group_id: int) -> GroupResponse:
        """
        Get response containing information about the group
        """
        resp = self.__client.request(
            self.__api.op['get_universe_groups_group_id'](
                group_id=group_id))
        return GroupResponse(resp)

    def get_group_multi(self, group_ids: List[int]) -> List[GroupResponse]:
        ops = []
        for group_id in group_ids:
            ops.append(self.__api.op['get_universe_groups_group_id'](
                group_id=group_id))

        response_infos = self.__client.multi_request(ops)
        return [GroupResponse(info[1]) for info in response_infos]

    def get_types(self) -> List[TypesResponse]:
        """
        Get response containing a list of all type ids
        """
        resp = self.__client.head(
            self.__api.op['get_universe_types'](page=1))
        if (resp.status != 200):
            raise APIException("", resp.status)

        pages = 1
        if 'X-Pages' in resp.header:
            pages = int(resp.header['X-Pages'][0])

        ops = []
        for page in range(1, pages+1):
            ops.append(self.__api.op['get_universe_types'](page=page))

        responses = self.__client.multi_request(ops)

        response_list: List[TypesResponse] = []
        for data_tuple in responses:  # (request, response)
            response_list.append(TypesResponse(data_tuple[1]))

        return response_list

    def get_type(self, type_id: int) -> TypeResponse:
        """
        Get response containing information about the type
        """
        resp = self.__client.request(
            self.__api.op['get_universe_types_type_id'](
                type_id=type_id))
        return TypeResponse(resp)

    def get_type_multi(self, type_ids: List[int]) -> List[TypeResponse]:
        ops = []
        for type_id in type_ids:
            ops.append(self.__api.op['get_universe_types_type_id'](
                type_id=type_id))

        response_infos = self.__client.multi_request(ops)
        return [TypeResponse(info[1]) for info in response_infos]
