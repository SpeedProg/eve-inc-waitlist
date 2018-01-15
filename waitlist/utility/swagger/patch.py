import time

import logging
import warnings
from collections import namedtuple
from datetime import datetime
from email._parseaddr import parsedate

from esipy.cache import DictCache, BaseCache, DummyCache
from esipy.events import api_call_stats
from esipy.exceptions import APIException
from flask_login import current_user
from pyswagger.core import BaseClient
from requests import Session, Request
import six
from requests.adapters import HTTPAdapter

from waitlist import db

logger = logging.getLogger(__name__)


class DummyResp(object):
    def __init__(self, resp, status_code):
        self.data = resp
        self.status = status_code


class EsiClient(BaseClient):

    __schemes__ = {'https'}

    __image_server__ = {
        'singularity': 'https://image.testeveonline.com/',
        'tranquility': 'https://imageserver.eveonline.com/',
    }

    def __init__(self, security=None, **kwargs):
        """ Init the ESI client object
        :param security: (optional) the security object [default: None]
        :param headers: (optional) additional headers we want to add
        :param transport_adapter: (optional) an HTTPAdapter object / implement
        :param cache: (optional) esipy.cache.BaseCache cache implementation.
        :param raw_body_only: (optional) default value [False] for all requests
        """
        super(EsiClient, self).__init__(security)

        # lets get rid of all our kwargs
        headers = kwargs.pop('headers', {})
        transport_adapter = kwargs.pop('transport_adapter', None)
        # initiate the cache object
        if 'cache' not in kwargs:
            self.cache = DictCache()
        else:
            cache = kwargs.pop('cache')
            if isinstance(cache, BaseCache):
                self.cache = cache
            elif cache is None:
                self.cache = DummyCache()
            else:
                raise ValueError('Provided cache must implement BaseCache')

        # store default raw_body_only in case user never want parsing
        self.raw_body_only = kwargs.pop('raw_body_only', False)

        self.timeout = kwargs.pop('timeout', 10)

        self.security = security
        self._session = Session()

        # check for specified headers and update session.headers

        if 'User-Agent' not in headers:
            headers['User-Agent'] = (
                'EsiPy/Client - '
                'https://github.com/Kyria/EsiPy'
            )
        self._session.headers.update({"Accept": "application/json"})
        self._session.headers.update(headers)

        # transport adapter
        if isinstance(transport_adapter, HTTPAdapter):
            self._session.mount('http://', transport_adapter)
            self._session.mount('https://', transport_adapter)

    def request(self, req_and_resp, raw_body_only=None, opt=None):
        """ Take a request_and_response object from pyswagger.App and
        check auth, token, headers, prepare the actual request and fill the
        response
        Note on performance : if you need more performance (because you are
        using this in a batch) you'd rather set raw_body_only=True, as parsed
        body is really slow. You'll then have to get data from response.raw
        and convert it to json using "json.loads(response.raw)"
        :param req_and_resp: the request and response object from pyswagger.App
        :param raw_body_only: define if we want the body to be parsed as object
                              instead of staying a raw dict. [Default: False]
        :param opt: options, see pyswagger/blob/master/pyswagger/io.py#L144
        :return: the final response.
        """

        if opt is None:
            opt = {}

        try:
            # required because of inheritance
            request, response = super(EsiClient, self).request(req_and_resp, opt)
        except APIException as e:
            logger.info("Failed to execute request",  e)
            ermsg = "No Message"
            if 'error' in e.response:
                ermsg = e.response['error']
            elif 'message' in e.response:
                ermsg = e.response['message']

            if e.status_code == 400 and ermsg == "invalid_token":
                # since the token is invalid lets delete it
                db.session.remove(current_user.ssoToken)
                db.session.commit()

            # fake a response that has the fields as expected
            return DummyResp(e.response, e.status_code)

        # check cache here so we have all headers, formed url and params
        cache_key = self.__make_cache_key(request)
        cached_response = self.cache.get(cache_key, None)

        if request.method == "GET" and cached_response is not None:
            res = cached_response

        else:
            # apply request-related options before preparation.
            request.prepare(
                scheme=self.prepare_schemes(request).pop(),
                handle_files=False
            )
            request._patch(opt)

            # prepare the request and make it.
            prepared_request = self._session.prepare_request(
                Request(
                    method=request.method.upper(),
                    url=request.url,
                    params=request.query,
                    data=request.data,
                    headers=request.header
                )
            )
            start_api_call = time.time()
            res = self._session.send(
                prepared_request,
                stream=True,
                timeout=self.timeout
            )

            # event for api call stats
            api_call_stats.send(
                url=res.url,
                status_code=res.status_code,
                elapsed_time=time.time() - start_api_call,
                message=res.content if res.status_code != 200 else None
            )

            if request.method == "GET" and res.status_code == 200:
                self.__cache_response(cache_key, res)

        if raw_body_only is None:
            response.raw_body_only = self.raw_body_only
        else:
            response.raw_body_only = raw_body_only

        response.apply_with(
            status=res.status_code,
            header=res.headers,
            raw=six.BytesIO(res.content).getvalue()
        )

        if 'warning' in res.headers:
            # send in logger and warnings, so the user doesn't have to use
            # logging to see it (at least once)
            logger.warning("[%s] %s" % (res.url, res.headers['warning']))
            warnings.warn("[%s] %s" % (res.url, res.headers['warning']))

        return response

    def __cache_response(self, cache_key, res):
        if 'expires' in res.headers:
            # this date is ALWAYS in UTC (RFC 7231)
            epoch = datetime(1970, 1, 1)
            expire = (
                datetime(
                    *parsedate(res.headers['expires'])[:6]
                ) - epoch
            ).total_seconds()
            now = (datetime.utcnow() - epoch).total_seconds()
            cache_timeout = int(expire) - int(now)

        else:
            # if no expire, define that there is no cache
            # -1 will be now -1sec, so it'll expire
            cache_timeout = -1

        # create a named tuple to store the data
        CachedResponse = namedtuple(
            'CachedResponse',
            ['status_code', 'headers', 'content']
        )
        self.cache.set(
            cache_key,
            CachedResponse(
                status_code=res.status_code,
                headers=res.headers,
                content=res.content,
            ),
            cache_timeout,
        )

    @classmethod
    def __make_cache_key(cls, request):
        headers = frozenset(request._p['header'].items())
        path = frozenset(request._p['path'].items())
        query = frozenset(request._p['query'])
        body = frozenset(request._p['body'])
        method = request.method
        return request.url, method, headers, path, query, body


def monkey_patch_pyswagger_requests_client():
    import esipy
    esipy.EsiClient = EsiClient
