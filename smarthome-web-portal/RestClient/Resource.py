# -*- coding: utf-8 -*-
"""
A resource wrapper to send http requests
"""
import logging
from RestClient.api.IoTClient import IoTClient
from utils.config import config

logger = logging.getLogger(__name__)


class Resource(object):
    _client = None

    def __init__(self, gateway_id):
        self.connect(gateway_id)

    def connect(self, gateway_id):
        """
        Connect to IoT web service
        """
        if self._client is None:
            self._client = IoTClient(gateway_id, proxies=config.get_all_proxy())

    def list_resource(self):
        """
        Return all the resources discovered in the network
        """
        result = self._client.get('/res')

        sensors = []
        if result.ok():
            for item in result:
                """
                sample response in json
                [
                  {
                    "di": "d38d75a3-f1be-4d2d-b084-e943005fbf8d",
                    "links": [
                      {
                        "href": "/a/fan",
                        "rt": ["oic.r.fan",]
                        "if": "o",
                        "p": {
                            "bm": 3,
                            "secure": false
                        }
                      }
                    ]
                  }
                ]
                """
                try:
                    href = str(item['links'][0]['href'])
                    # todo: parse multiple sensor types
                    rt = str(item['links'][0]['rt'][0])

                    # by default, obs is True
                    observable = True
                    # check whether policy param is supported
                    if item['links'][0].get('p'):
                        bm = item['links'][0]['p']['bm']
                        secure = item['links'][0]['p']['secure']

                        if bm == 1 and not secure:
                            observable = False
                        elif bm == 3 and not secure:
                            observable = True

                    if rt and not rt.startswith("oic.wk") and href \
                            and (href.startswith("/a/") or href.startswith("/brillo/")):
                        sensors.append((item['di'], href, rt, observable))
                    else:
                        # ignore the wrong or unregistered json types
                        pass
                except:
                    logging.error("Failed to get resources: index out of range. ")

        else:
            logging.error("Failed to get resources: {}".format(str(result.errors())))
        return sensors

    def list_device(self):
        """
            Return all the devices discovered in the network
        """
        result = self._client.get('/d')

        devices = dict()
        if result.ok():
            for item in result:
                """
                sample response in json
                [{
                    di: "de356706-13cf-49b5-a023-f1f45079ff72",
                    n: "Smart Home Fan",
                    icv: "core.1.1.0"
                },]
                """
                try:
                    device_id = str(item['di'])
                    device_name = str(item['n'])
                    devices[device_id] = device_name
                except:
                    logging.error("Failed to get device: index out of range. ")
        else:
            logging.error("Failed to get devices: {}".format(str(result.errors())))
        return devices





