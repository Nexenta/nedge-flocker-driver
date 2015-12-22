# Copyright Nexenta Systems, Inc.

"""
Main test driver for NexentaEdge.
"""

import os
import yaml
import socket

from twisted.trial.unittest import SkipTest
from nedge_flocker_plugin.nedge_objstor import NedgeBlockDeviceAPI, NedgeConfig


def read_nedge_config():
    config_file = os.getenv('NEDGE_FLOCKER_CONFIG_FILE',
                            '/etc/flocker/nedge.yml')
    with open(config_file) as fh:
        config = yaml.load(fh.read())
        nedge_config = config['nedge']
        nedge_cluster_id = nedge_config['cluster_id']
        nedge_tenant_id = nedge_config['tenant_id']
        nedge_bucket_id = nedge_config['bucket_id']
        nedge_chunk_sz = nedge_config['chunk_sz']
        return NedgeConfig(nedge_cluster_id, nedge_tenant_id,
                           nedge_bucket_id, nedge_chunk_sz)
    raise SkipTest('Could not open config file')


def nedge_test(test_case):
    conf = read_nedge_config()
    nbapi = NedgeBlockDeviceAPI(
        conf, compute_instance_id=unicode(socket.gethostname()),
        allocation_unit=4096)
    return nbapi
