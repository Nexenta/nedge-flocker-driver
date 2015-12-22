# Copyright Nexenta Systems, Inc.
# See LICENSE file for details.

from flocker.node import BackendDescription, DeployerType
from nedge_flocker_plugin.nedge_objstor import (
	get_nedge_block_api, NedgeConfig)


def api_factory(**kwargs):
    conf = NedgeConfig(cluster_id=kwargs[u'cluster_id'],
                       tenant_id=kwargs[u'tenant_id'],
                       bucket_id=kwargs[u'bucket-id'],
                       chunk_sz=kwargs[u'chunk_sz'])
    return get_nedge_block_api(conf)

# NEDGE has its own cluster id. We don't need flocker cluster id
# Hence needs_cluster_id=False
# If needed in future we may have to use flocker-cluster-id separately
FLOCKER_BACKEND = BackendDescription(
                      name=u'nedge_flocker_plugin', needs_reactor=False,
                      needs_cluster_id=False, api_factory=api_factory,
                      deployer_type=DeployerType.block)
