# -*- coding: utf-8 -*-
"""
Task to fetch data
"""
import threading
import time
from utils.util import gen_randint
from RestClient import Resource as rsclient
from DB.api import resource, sensor_type
from CeleryTask.managers import base
from RestClient.api.iotError import IoTConnectionError
from DB import exception
from CeleryTask.managers.fetch_data import FetchData


class DataManager(base.BaseTask):
    """The task class to collect and update resources
        and pull each device data by thread
    """
    RESOURCE_UPDATE_INTERVAL = 10
    MAX_THREAD = 20

    def __init__(self, gateway_id):
        self._client = None
        self._sensor_type_map = DataManager.get_sensor_types_map()
        # self.username = username
        self.gateway_id = gateway_id
        self.devices = dict()

    @staticmethod
    def get_sensor_types_map():
        types = sensor_type.get_all_types()
        mapping = {t_dict['type']: t_dict['id'] for t_dict in types}
        return mapping

    def _connect(self):
        if not self._client:
            self._client = rsclient.Resource(self.gateway_id)

    def _get_devices(self):
        """get all devices in the network """
        self._connect()
        return self._client.list_device()

    def _get_active_resource(self):
        """
        Get active resource in db
        return a tuple (di, path)
        """
        self._connect()
        return self._client.list_resource()

    def update_resource(self, active_resource=[]):
        """
        Pull resource and update their status in db
        :param: active_resource: tuple, (uuid, href, resource_type, obs)
        """
        active_resource_ids = []
        for i, v in enumerate(active_resource):
            uuid, href, typ, obs = v[0], v[1], v[2], v[3]
            if typ not in self._sensor_type_map.keys():
                typ = "generic"

            try:
                ret = resource.get_resource(exception_when_missing=False, path=href, uuid=uuid)
            except IoTConnectionError:
                continue

            if not ret:
                if typ == "generic" and uuid not in self.devices.keys():
                    self.devices = self._get_devices()
                    self.log.info('Update device list: {}'.format(str(self.devices)))

                ret = resource.add_resource({
                    'uuid': uuid,
                    'sensor_type_id': self._sensor_type_map[typ],
                    'gateway_id': self.gateway_id,
                    'status': True,
                    'path': href,
                    'tag': self.devices.get(uuid) if typ == "generic" and self.devices.get(uuid) else None,
                    'observable': obs
                })
                self.log.info('Resource {} is added.'.format(str(ret)))
                active_resource_ids.append(ret.get('id'))
            elif not ret.get('status'):
                # update resource status
                resource.update_resource(ret.get('id'), status=True)
                active_resource_ids.append(ret.get('id'))
            else:
                active_resource_ids.append(ret.get('id'))
            active_resource[i] = v + (ret.get('id'), )
        self._update_resource(active_resource_ids)

    def _update_resource(self, active_resource_ids=[]):
        for res in resource.list_resource(status=True, gateway_id=self.gateway_id):
            res_id = res.get('id')
            # res_uuid = res.get('uuid')
            if res_id and res_id not in active_resource_ids:
                resource.update_resource(res_id, status=False)

    def _fetch_data(self):
        """
        Resource connection pool management
        """
        connections = {}
        while True:
            self.log.debug('---begin for loop---')
            try:
                ls = self._get_active_resource()
                self.update_resource(ls)
                # print ls
                self.log.debug("{}".format(str(ls)))
            except exception.DatabaseException:
                time.sleep(2)
                continue

            # remove dead threads in the conn pool
            main_thread = threading.currentThread()
            running_id = [th.getName() for th in threading.enumerate() if th is not main_thread and th.is_alive()]
            self.log.info('running ids: {}, total: {}'.format(str([rid for rid in running_id]), len(running_id)))

            dead_id = set(connections.keys()) - set(running_id)
            for rid in dead_id:
                self.log.info("Thread {} is dead. Remove it from the connection pool. ".format(rid))
                del connections[rid]
            self.log.info('dead ids: ' + str(dead_id))

            # latest resource ids pulled from the gateway
            existing_id_list = [str(rid) for di, href, rt, obs, rid in ls if rid is not None]

            # find threads with obsolete ids and remove them
            zombie_id = set(connections.keys()) - set(existing_id_list)
            for rid in zombie_id:
                self.log.info("kill zombie threads: {}".format(rid))
                connections[rid].kill()
                del connections[rid]

            self.log.info('active threads: {}, total: {}'.format(str([rid for rid in connections.keys()]),
                                                                 len(connections.keys())))

            for di, href, rt, obs, rid in ls:
                if rid and str(rid) not in connections.keys() and str(rid) not in running_id:
                    if len(connections) >= self.MAX_THREAD:
                        # quit the loop cos it exceeds max threads limit
                        self.log.info("Exceeded maximal thread threshold {}, queuing request "
                                      "for {}?di={}".format(self.MAX_THREAD, href, di))
                        self.log.info(connections.keys())
                        break
                    time.sleep(gen_randint(0, 5))
                    t = FetchData(self.gateway_id, (href, di, obs))
                    connections[str(rid)] = t
                    self.log.info('threads in the pool: ' + str(connections))
                # logging.debug('end of for.')

            self.log.debug('---sleep 10 secs---')
            time.sleep(self.RESOURCE_UPDATE_INTERVAL)

    def run(self):
        self._fetch_data()


if __name__ == '__main__':
    task = DataManager('dev')
    task.run()

