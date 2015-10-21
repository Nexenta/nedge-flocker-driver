# Copyright Nexenta Systems, Inc.
#Check LICENSE file

from flocker.node.agents.blockdevice import (
    VolumeException, AlreadyAttachedVolume,
    UnknownVolume, UnattachedVolume,
    IBlockDeviceAPI, _blockdevicevolume_from_dataset_id,
    _blockdevicevolume_from_blockdevice_id
)

from eliot import Message, Logger
from twisted.python.filepath import FilePath
from zope.interface import implementer
import os
import socket
import requests

_logger = Logger()

class NedgeConfig(object):
    def __init__(self, cluster_id, tenant_id, bucket_id, chunk_sz):
        self._cluster_id = cluster_id
        self._tenant_id = tenant_id
        self._bucket_id = bucket_id
        self._chunk_sz = chunk_sz
	self.cdnbd_url = 'http://127.0.0.1:8080/nbd'
	self.adttnbd_url = 'http://127.0.0.1:8080/nbd/register'

    def get_chunk_sz(self):
        return self._chunk_sz

    def get_clust_id_str(self):
        return str(self._cluster_id)

    def get_tenant_id_str(self):
        return str(self._tenant_id)

    def get_bucket_id_str(self):
        return str(self._bucket_id)

    def get_objpath_str(self, idx):
        return self.get_clust_id_str() + '/' + \
               self.get_tenant_id_str() + '/' + \
               self.get_bucket_id_str() + '/' + str(idx)

@implementer(IBlockDeviceAPI)
class NedgeBlockDeviceAPI(object):

    def __init__(self, nedge_conf, compute_instance_id=socket.gethostname(),
                 allocation_unit=4096):
        self._config = nedge_conf
        self._node_id = compute_instance_id
        self._chunk_sz = allocation_unit
        self._objs_list = {}
        self._reqdata = {}

    def _get_vol(self, blockdevice_id):
        try:
            vol = self._objs_list[str(blockdevice_id)]
            if vol is not None:
                return vol
            else:
                raise UnknownVolume(blockdevice_id)
        except:
            raise UnknownVolume(blockdevice_id)

    def compute_instance_id(self):
        return self._node_id

    def allocation_unit(self):
        return self._chunk_sz

    def create_volume(self, dataset_id, size):
        volume = _blockdevicevolume_from_dataset_id(size=size,
                                                    dataset_id=dataset_id)
        obj_idx = len(self._objs_list)
        self._reqdata.clear();
        self._reqdata['number'] = obj_idx
        self._reqdata['volSizeMB'] = size >> 20
        self._reqdata['blockSize'] = 512
        self._reqdata['chunkSize'] = self._chunk_sz
        self._reqdata['objectPath'] = self._config.get_objpath_str(obj_idx)

        resp = requests.post(self._config.cdnbd_url, self._reqdata)
        if resp.status_code > 199 and resp.status_code < 300:
            self._objs_list[str(volume.blockdevice_id)] = volume
        else:
            volume = None

        return volume

    def destroy_volume(self, blockdevice_id):
        try:
            volume = self._get_vol(blockdevice_id)
            obj_idx = self._objs_list.values().index(volume)
            self._objs_list.pop(str(blockdevice_id), None)

            self._reqdata.clear();
            self._reqdata['number'] = obj_idx
            self._reqdata['objectPath'] = self._config.get_objpath_str(obj_idx)
            resp = requests.delete(self._config.cdnbd_url, data=self._reqdata)
            if resp.status_code != requests.codes.ok:
                Message.new(resp.text).write(_logger)
        except:
            raise

    def destroy_volume_folder(self):
        #Do nothing for now
        return

    def attach_volume(self, blockdevice_id, attach_to):
        try:
            volume = self._get_vol(blockdevice_id)
            if volume.attached_to is None:
                obj_idx = self._objs_list.values().index(volume)
                self._reqdata.clear();
                self._reqdata['number'] = obj_idx
                self._reqdata['objectPath'] = self._config.get_objpath_str(obj_idx)

                resp = requests.post(self._config.adttnbd_url, self._reqdata)
                if resp.status_code == 204:
                    att_vol = volume.set(attached_to=unicode(attach_to))
                    self._objs_list[str(blockdevice_id)] = att_vol
                else:
                    att_vol = None
                return att_vol
            else:
                raise AlreadyAttachedVolume(blockdevice_id)
        except:
            raise

    def resize_volume(self, blockdevice_id, size):
        #Do nothing for now
        return

    def detach_volume(self, blockdevice_id):
        try:
            volume = self._get_vol(blockdevice_id)
            if volume.attached_to is not None:
                obj_idx = self._objs_list.values().index(volume)
                self._reqdata.clear();
                self._reqdata['number'] = obj_idx
                self._reqdata['objectPath'] = self._config.get_objpath_str(obj_idx)

                resp = requests.delete(self._config.adttnbd_url, data=self._reqdata)
                if resp.status_code == requests.codes.ok:
                    dtt_vol = volume.set(attached_to=None)
                    self._objs_list[str(blockdevice_id)] = dtt_vol
            else:
                Message.new(Info='Volume' + blockdevice_id + 'not attached').write(_logger)
                raise UnattachedVolume(blockdevice_id)
        except:
            raise

    def list_volumes(self):
        return self._objs_list.values()

    def get_device_path(self, blockdevice_id):
        try:
            volume = self._get_vol(blockdevice_id)
            if volume.attached_to is not None:
                return FilePath('/dev/nbd' + \
                                str(self._objs_list.values().index(volume)))
            else:
                Message.new(Info='Volume' + blockdevice_id + 'not attached').write(_logger)
                raise UnattachedVolume(blockdevice_id)
        except:
            raise

def get_nedge_block_api(conf):
    return NedgeBlockDeviceAPI(conf,
                compute_instance_id=unicode(socket.gethostname()),
                allocation_unit=conf.get_chunk_sz())
