NexentaEdge Flocker Plugin
==========================
The plugin for NexentaEdge Flocker integration.

## Description
ClusterHQ/Flocker provides an efficient and easy way to connect persistent store with Docker containers. This project provides a plugin to provision NexentaEdge object storage.

##Installation
Make sure that flocker node service has been installed
(https://docs.clusterhq.com/en/1.2.0/install/install-node.html)
/opt/flocker/bin/python2.7 setup.py install

##Testing
Create a configuration file: /etc/flocker/nedge.yml.
Example:
nedge:
    "cluster_id": "cltest"
    "tenant_id": "test"
    "bucket_id": "ccowbd"
    "chunk_sz": 4096

To run the tests, enter-
    trial tests.nedge_tests
    or
    /opt/flocker/bin/trial tests.nedge_tests
(trial is a python program that runs unit-tests. You must in
 <prefix>/nedge-flocker-driver directory.)

##Usage
Add the following section to the file '/etc/flocker/agent.yml':
"dataset":
    "backend": "nedge_flocker_plugin"
    "cluster_id": "cltest"
    "tenant_id": "test"
    "bucket-id": "ccowbd"
    "chunk_sz": 4096
(This is an example. Use your own values)

##Note
The cluster_id, tenant_id and bucket_id must exist, before running the test
or flocker
