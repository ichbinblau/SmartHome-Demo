# -*- coding: utf-8 -*-
"""
Http Client
"""
import logging
import json
import socket
import ssl

from requests import Session
from requests.exceptions import ConnectionError, ReadTimeout, SSLError, ChunkedEncodingError
import requests.packages.urllib3

from RestClient import __version__
from iotError import IoTConnectionError, IoTRequestError

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class ApiClient(object):
    """
    A client to access a RESTful API or streaming resources
    """
    header = {}
    stream_timeout = None
    conn_timeout = 10
    rest_timeout = 30

    def __init__(self, api_uri, proxy, ca_cert=None):
        """
        Create a RESTful API client.
        """
        self.api_uri = api_uri
        self.proxy = None
        self.auth = None
        self.verify = None
        if proxy:
            if isinstance(proxy, dict):
                self.proxy = proxy
            elif isinstance(proxy, str):
                self.proxy = {
                    'http': proxy,
                    'https': proxy
                }
        if ca_cert:
            self.verify = ca_cert

    def version(self):
        return __version__

    def add_header(self, key, value):
        self.header[key] = value

    def set_basic_auth(self, username=None, password=None):
        self.auth = (username, password)

    def _set_default_header(self):
        from platform import platform, python_version
        self.add_header('User-Agent', "PythonClient/{0} ({1}; Python {2})".format(self.version(),
                                                                                  platform(True),
                                                                                  python_version()))
        self.add_header('Connection', 'keep-alive')

    @staticmethod
    def merge_dicts(*dict_args):
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)

        return result

    def request(self, method, path, data={}, headers={}, stream=False):
        url = '{0}{1}'.format(self.api_uri, path)
        print url
        params = {}
        self._set_default_header()
        headers = self.merge_dicts(self.header, headers)
        logger.debug("url:" + url)

        with Session() as s:
            s.headers = headers
            s.stream = stream
            s.auth = self.auth if self.auth else None

            if stream:
                timeout = self.stream_timeout
            else:
                timeout = self.rest_timeout

            if method in ('POST', 'PUT'):
                params = None
            else:
                params.update(data)
                data = None

            s.verify = self.verify if self.verify else False

            try:
                r = s.request(
                    method,
                    url,
                    data=data,
                    params=params,
                    timeout=(self.conn_timeout, timeout),
                    # verify=get_full_path(os.path.join('certs', 'certificate.pem')),
                    proxies=self.proxy)
            except (ConnectionError, ReadTimeout, SSLError,
                    ssl.SSLError, socket.error) as e:
                raise IoTConnectionError(e)
            return IoTResponse(r, stream)

    def post(self, path, data={}):
        return self.request("POST", path, data, {'Content-Type': 'application/json'})

    def get(self, path, data={}, stream=False):
        return self.request("GET", path, data, stream=stream)

    def put(self, path, data={}):
        return self.request("PUT", path, data, {'Content-Type': 'application/json'})

    def delete(self, path, data={}):
        return self.request("DELETE", path, data)


class IoTResponse(object):
    def __init__(self, response, stream=False):
        self.response = response
        self.stream = stream
        self._stop = False
        self.content = None
        if not self.stream:
            try:
                self.content = self.response.json()
            except ValueError:
                self.content = self.response.text

    @property
    def headers(self):
        """returns: Dictionary of API response header contents."""
        return self.response.headers

    @property
    def status_code(self):
        """returns: HTTP response status code."""
        return self.response.status_code

    @property
    def text(self):
        """returns: Raw API response text."""
        return self.response.text

    @property
    def json(self):
        """returns: response as JSON object."""
        return self.response.json()

    def ok(self):
        """return: whether the response status is true """
        import requests
        return self.response.status_code in (requests.codes.ok,
                                             requests.codes.created,
                                             requests.codes.no_content)

    def errors(self):
        """return: http response errors as dict"""
        if self.ok():
            return {}

        errors = self.content
        if not isinstance(errors, dict):
            # convert to dict for consistency
            errors = {"error": errors}
        elif 'errors' in errors:
            errors = errors['errors']

        return errors

    def __getitem__(self, key):
        return self.content[key]

    def __len__(self):
        return len(self.content)

    def get_data(self, parser=None, **kargs):
        """Get streaming data
        param: parser, callback function to parse the streaming data
        """
        if not self.ok():
            raise IoTRequestError(self.status_code)

        if self.stream:
            try:
                # read data as it arrives in whatever size the chunks are received if chunk_size is None
                for chunk in self.response.iter_content(chunk_size=4096):
                    if self._stop:
                        break
                    if chunk:
                        if parser:
                            parser(json.loads(chunk), **kargs)
                        else:
                            print chunk
            except ChunkedEncodingError as ex:
                raise IoTConnectionError(ex)
            except (ConnectionError, ReadTimeout, SSLError,
                    ssl.SSLError, socket.error, ChunkedEncodingError) as e:
                raise IoTConnectionError(e)
        else:
            return self.content

    def close(self):
        """Disconnect stream connection"""
        self._stop = True

if __name__ == "__main__":
    import datetime
    p = "child-prc.intel.com:913"
    proxy = {
        'http': p,
        'https': p
    }
    now = datetime.datetime.now()
    client = ApiClient("https://10.239.76.11:8000/api/oic",
                       proxy=proxy)
    end = datetime.datetime.now()
    print end - now
    resp = client.get("/a/illuminance?di=c6ecba70-e72d-41c2-8657-1fb94ab29399&obs=1", stream=True)
    resp.get_data()
