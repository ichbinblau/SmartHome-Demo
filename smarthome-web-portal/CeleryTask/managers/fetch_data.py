# -*- coding: utf-8 -*-
"""
Thread class for data processing
"""
import threading
import time
import json
from RestClient import sensor as client
from utils.util import get_class
from RestClient.api.NexmoClient import NexmoClient
from DB.api import resource
from RestClient.api.iotError import IoTConnectionError


class FetchData(threading.Thread):
    """Threaded device observer and parser.
    Username: username
    Resource_info: (href, dev_id, resource_id)
    """
    def __init__(self, gateway_id, resource_info):
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.gateway_id = gateway_id
        self.href = resource_info[0]
        self.dev_id = resource_info[1]
        self.obs = resource_info[2]
        self.client_conn = None
        self.start()

    def __repr__(self):
        return "%s" % self.href

    def connect(self):
        self.client_conn = client.Sensor(self.dev_id, self.href, self.gateway_id)

    def run(self):
        try:
            # grabs urls of hosts and print data
            print("{}?di={}".format(self.href, self.dev_id))
            # ret = self.client.get("{}?di={}".format(typ, dev_id), {'obs': 1}, stream=True)
            self.connect()
            res = resource.get_resource(exception_when_missing=False, path=self.href, uuid=self.dev_id, status=True)
            if not res:
                return
            self.name = res.get('id')
            kargs = {
                'sensor': res.get('sensor_type').get('mapping_class'),
                'resource_id': res.get('id'),
                'uuid': self.dev_id,
                'gateway_id': self.gateway_id,
            }

            if self.obs:
                # observable
                self.client_conn.get_data(stream=True, callback=self.parse_data, **kargs)
            else:
                # not observable
                while True and not self.event.is_set():
                    data = self.client_conn.get_data()
                    self.parse_data(data, **kargs)
                    time.sleep(3)

        except IoTConnectionError as e:
            raise Exception("There was an error connecting to %s: %s : %r" % (self.dev_id, self.href, e))

    def kill(self):
        if self.obs:
            self.client_conn.terminate()
        else:
            self.event.set()

    @staticmethod
    def parse_data(data, **kargs):
        """parse the json data and save them in db."""
        if data:
            sensor = kargs.get('sensor')
            uuid = kargs.get('uuid')
            gateway_id = kargs.get('gateway_id')
            resource_id = kargs.get('resource_id')
            if sensor == 'power':
                power_add = get_class("DB.api.power.new")
                energy_add = get_class("DB.api.energy.new")

                new_energy = data.get('power1')
                new_power = data.get('power2')

                if new_power != 0:
                    content = {
                            'resource_id': resource_id,
                            'value': int(new_power),
                    }
                    # power_add(content)
                    print('update power: {}'.format(str(power_add(content))))

                if new_energy != 0:
                    content = {
                            'resource_id': resource_id,
                            'value': int(new_energy),
                    }
                    # energy_add(content)
                    print('update energy: {}'.format(str(energy_add(content))))
            else:
                add_method = get_class("DB.api.{}.new".format(sensor))
                status_method = get_class("DB.api.{}.get_latest_by_gateway_uuid".format(sensor))

                content = {
                    'resource_id': resource_id,
                }

                if sensor == 'solar':
                    new_tilt = data.get('tiltPercentage')
                    if new_tilt is not None:
                        content.update({
                            'tiltpercentage': new_tilt,
                            'lcd_first': data.get('lcd1'),
                            'lcd_second': data.get('lcd2'),
                        })

                        # add_method(content)
                        print('update tilt percentage: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get tilt percentage.")
                elif sensor == 'illuminance':
                    new_ill = data.get('illuminance')
                    if new_ill is not None:
                        content.update({
                            'illuminance': new_ill,
                        })
                        # add_method(content)
                        print('update illuminance: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get Illuminance status.")
                elif sensor == 'temperature':
                    new_temp = data.get('temperature')
                    if new_temp is not None:
                        content.update({
                            'temperature': new_temp,
                            'units': data.get('units'),
                            'range': data.get('range'),
                        })

                        # add_method(content)
                        print('update temperature: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get Temperature status.")
                elif sensor == 'audio':
                    if data is not None:
                        content.update({
                            'mute': data.get('mute'),
                            'volume': data.get('volume'),
                        })
                        # add_method(content)
                        print('update audio: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get Audio sensor status .")
                elif sensor == 'brightness':
                    if data is not None:
                        content.update({
                            'brightness': data.get('brightness'),
                        })
                        # add_method(content)
                        print('update brightness: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get Brightness sensor status .")
                elif sensor == 'mp3player':
                    if data is not None:
                        content.update({
                            'media_states': json.dumps(data.get('mediaStates')),
                            'playlist': json.dumps(data.get('playList')),
                            'state': data.get('state'),
                            'title': data.get('title'),
                        })
                        # add_method(content)
                        print('update mp3player: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get Mp3player sensor status .")
                elif sensor == 'rgbled':
                    new_rgb = data.get('rgbValue')
                    if new_rgb is not None:
                        content.update({
                            'rgbvalue': str(new_rgb),
                            'range': str(data.get('range')),
                        })
                        # add_method(content)
                        print('update rdbled: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get Rgbled status .")
                elif sensor == 'environment':
                    if data is not None:
                        content.update({
                            'temperature': data.get('temperature'),
                            'pressure': data.get('pressure'),
                            'humidity': data.get('humidity'),
                            'uv_index': data.get('uvIndex'),
                        })
                        # add_method(content)
                        print('update environment: {}'.format(str(add_method(content))))
                    else:
                        print("Unable to get Environment sensor status .")
                elif sensor == 'generic':
                    if data is not None:
                        content.update({
                            'json_data': json.dumps(data),
                        })
                        # add_method(content)
                        print('update generic {}: {}'.format(data.get('id'), str(add_method(content))))
                    else:
                        print("Unable to get Generic sensor {} status .".format(data.get('id')))
                else:
                    obj = status_method(resource_id)
                    status = bool(obj.get('status')) if obj else None
                    new_sts = bool(data.get('value'))
                    if status != new_sts:
                        content.update({
                            'status': new_sts,
                        })
                        print('update {} data: {}'.format(sensor, str(add_method(content))))
                        if new_sts and NexmoClient.send_message(gateway_id, uuid, sensor):
                            print('Sent text alert to users for {} status is True.'.format(sensor))
                    else:
                        print("{} status {} has not been changed.".format(sensor, new_sts))
