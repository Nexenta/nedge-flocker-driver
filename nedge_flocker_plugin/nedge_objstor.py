# Copyright Nexenta Systems, Inc.
# Check LICENSE file
import json

from flocker.node.agents.blockdevice import (
    AlreadyAttachedVolume,
    UnknownVolume, UnattachedVolume,
    IBlockDeviceAPI, BlockDeviceVolume, get_blockdevice_volume
)

from uuid import UUID
from eliot import Message, Logger, start_action
from twisted.python.filepath import FilePath
from zope.interface import implementer
import socket
import requests
import sqlite3

import jsonrpc

_logger = Logger()

VOLUME_PREFIX = 'volume-'


class SQLiteConnection(object):
    def __init__(self):
        self.con = None

    def __enter__(self):
        self.con = sqlite3.connect('/tmp/nedge_flocker_plugin.db')
        self.con.row_factory = sqlite3.Row
        return self.con

    def __exit__(self, type, value, traceback):
        self.con.commit()
        self.con.close()


class VolumeDataStore(object):
    def __init__(self):
        #SELECT name FROM sqlite_master WHERE type='table' AND name='table_name';
        with self.get_connection() as conn:
            table = '''create table if not exists volume(
            id text PRIMARY KEY, attached_to text
            )'''
            conn.execute(table)

    def get_connection(self):
        return SQLiteConnection()

    def as_dict(self):
        with self.get_connection() as conn:
            sql = 'select id, attached_to from volume'
            c = conn.cursor()
            c.execute(sql)
            d = {}
            for vol in c.fetchall():
                d[vol['id']] = vol['attached_to']
            return d

    def __iter__(self):
        return self.as_dict().__iter__()

    def __delitem__(self, key):
        sql = 'delete from volume where id=?'
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(sql, (key,))

    def __setitem__(self, key, value):
        with self.get_connection() as conn:
            Message.log(action="__setitem__", key=key, value=value)
            sql = 'insert or ignore into volume(attached_to, id) values(?, ?)'
            conn.execute(sql, (value, key))
            sql = 'update volume set attached_to=? where id=?'
            conn.execute(sql, (value, key))

    def __getitem__(self, key):
        Message.log(action="__getitem__", key=key)
        with self.get_connection() as conn:
            sql = 'select attached_to from volume where id=?'
            c = conn.cursor()
            c.execute(sql, (key,))
            res = c.fetchone()['attached_to']
            return res


class NedgeConfig(object):
    def __init__(self, nedge_mgt_address, cluster_id, tenant_id, bucket_id, chunk_sz):
        self._cluster_id = cluster_id
        self._tenant_id = tenant_id
        self._bucket_id = bucket_id
        self._chunk_sz = chunk_sz
        self.nedge_mgt_address = nedge_mgt_address
        self.cdnbd_url = 'http://{}:8080/nbd'.format(nedge_mgt_address)
        self.adttnbd_url = self.cdnbd_url + '/register'

    def get_chunk_sz(self):
        return self._chunk_sz

    def get_clust_id_str(self):
        return str(self._cluster_id)

    def get_tenant_id_str(self):
        return str(self._tenant_id)

    def get_bucket_id_str(self):
        return str(self._bucket_id)

    def get_objpath_str(self, idx):
        return '/'.join((self.get_clust_id_str(), self.get_tenant_id_str(), self.get_bucket_id_str(), str(idx)))


@implementer(IBlockDeviceAPI)
class NedgeBlockDeviceAPI(object):

    def __init__(self, nedge_conf, compute_instance_id=socket.gethostname(),
                 allocation_unit=4096):
        self._config = nedge_conf
        self._node_id = compute_instance_id
        self._chunk_sz = allocation_unit
        self.restapi = jsonrpc.NexentaEdgeJSONProxy(
            'http', self._config.nedge_mgt_address, 8080, '',
            'admin', 'nexenta')
        self.bucket_path = '/'.join((self._config._cluster_id, self._config._tenant_id, self._config._bucket_id))
        self.store = VolumeDataStore()

    def _get_host_info(self, host):
        res = self.restapi.get('system/stats')
        servers = res['stats']['servers']
        for sid in servers:
            if host == sid or host == servers[sid]['hostname']:
                return servers[sid]
        raise Exception('No %s hostname in NEdge cluster' % host)

    def _get_remote_url(self, host):
        return '?remote=' + str(self._get_host_info(host)['ipv6addr'])

    def _get_nbd_devices(self, host):
        rsp = self.restapi.get('sysconfig/nbd/devices' +
                               self._get_remote_url(host))
        return json.loads(rsp['value'])

    def _get_nbd_number(self, host, name):
        nbds = self._get_nbd_devices(host)
        for dev in nbds:
            if dev['objectPath'] == self.bucket_path + '/' + name:
                return dev['number']
        return -1

    def _get_volume_name(self, dataset_id):
        return '{}{}'.format(VOLUME_PREFIX, dataset_id)

    def compute_instance_id(self):
        self.log('compute_instance_id')
        return self._node_id

    def allocation_unit(self):
        self.log('allocation_unit')
        return self._chunk_sz

    def create_volume(self, dataset_id, size):
        with start_action(action_type='create_volume', dataset_id=dataset_id.get_hex(), size=size):
            volume_name = self._get_volume_name(dataset_id)
            self.restapi.post('nbd' + self._get_remote_url(self._node_id), {
                'objectPath': self._config.get_objpath_str(volume_name),
                'volSizeMB': size >> 20,
                'blockSize': 512,
                'chunkSize': self._chunk_sz
            })

            volume = BlockDeviceVolume(
                size=size, attached_to=None,
                dataset_id=dataset_id,
                blockdevice_id=volume_name.decode('utf8'))
            self.store[volume_name] = None
            return volume

    def destroy_volume(self, blockdevice_id):
        with start_action(action_type='destroy_volume', blockdevice_id=blockdevice_id):
            number = self._get_nbd_number(self._node_id, blockdevice_id)
            if number == -1:
                Message.log(
                    'Volume %(volume)s does not exist at %(path)s path' % {
                        'volume': blockdevice_id,
                        'path': self.bucket_path
                    })
                return
            self.restapi.delete('nbd' + self._get_remote_url(self._node_id), {
                'objectPath': self._config.get_objpath_str(blockdevice_id),
                'number': number
            })
            del self.store[blockdevice_id]

    def destroy_volume_folder(self):
        # Do nothing for now
        return

    def attach_volume(self, blockdevice_id, attach_to):
        with start_action(action_type='attach_volume', blockdevice_id=blockdevice_id, attach_to=attach_to):
            unattached_volume = get_blockdevice_volume(self, blockdevice_id)
            if unattached_volume.attached_to is not None:
                raise AlreadyAttachedVolume(blockdevice_id)
            attached_volume = unattached_volume.set('attached_to', attach_to)
            self.store[blockdevice_id] = attach_to
            return attached_volume
            '''
            volume = self._get_vol(blockdevice_id)
            if volume.attached_to is None:
                att_vol = volume.set(attached_to=attach_to)

                obj_idx = self._objs_list.values().index(volume)
                #self._reqdata.clear()
                _reqdata = {}
                _reqdata['number'] = obj_idx
                _reqdata['objectPath'] = self._config.get_objpath_str(obj_idx)

                resp = requests.post(self._config.adttnbd_url, _reqdata)
                if resp.status_code == 204:
                    att_vol = volume.set(attached_to=attach_to)
                    self._objs_list[str(blockdevice_id)] = att_vol
                else:
                    att_vol = None
                self.log('attach_volume end', att_vol=att_vol)'''


    def resize_volume(self, blockdevice_id, size):
        # Do nothing for now
        return

    def detach_volume(self, blockdevice_id):
        with start_action(action_type='detach_volume', blockdevice_id=blockdevice_id):
            attached_volume = get_blockdevice_volume(self, blockdevice_id)
            if attached_volume.attached_to is None:
                Message.log(Info='Volume {} is not attached'.format(blockdevice_id))
                raise UnattachedVolume(blockdevice_id)
            self.store[blockdevice_id] = None
            '''else:
                obj_idx = self._objs_list.values().index(volume)
                _reqdata = {}
                _reqdata['number'] = obj_idx
                _reqdata['objectPath'] = self._config.get_objpath_str(obj_idx)

                resp = requests.delete(self._config.adttnbd_url, data=_reqdata)
                if resp.status_code == requests.codes.ok:
                    dtt_vol = volume.set(attached_to=None)
                    self._objs_list[str(blockdevice_id)] = dtt_vol'''


    def list_volumes(self):
        volumes = []
        for vol_info in self._get_nbd_devices(self._node_id):
            blockdevice_id = vol_info["objectPath"].split('/')[-1]
            if blockdevice_id in self.store:
                volume = BlockDeviceVolume(
                    size=vol_info["volSize"], attached_to=self.store[blockdevice_id],
                    dataset_id=UUID(blockdevice_id[len(VOLUME_PREFIX):]),
                    blockdevice_id=blockdevice_id.decode('utf8'))
                volumes.append(volume)
        return volumes

    def get_device_path(self, blockdevice_id):
        number = self._get_nbd_number(self._node_id, blockdevice_id)
        if number == -1:
            raise UnknownVolume(blockdevice_id)
        if blockdevice_id not in self.store:
            raise UnattachedVolume(blockdevice_id)
        return FilePath('/dev/nbd' + str(number))


    def log(self, msg, **kwargs):
        for key in kwargs.keys():
            kwargs[key] = str(kwargs[key])
        kwargs['message'] = msg
        Message.new(**kwargs).write()


def get_nedge_block_api(conf):
    return NedgeBlockDeviceAPI(
        conf, compute_instance_id=unicode(socket.gethostname()),
        allocation_unit=conf.get_chunk_sz())
