[![Build Status](https://travis-ci.org/travis-ci/travis-web.svg?branch=master)](https://travis-ci.org/travis-ci/travis-web)
This driver has been tested with Flocker 1.7.2.

NexentaEdge Flocker Plugin
==========================
The plugin for NexentaEdge Flocker integration.


## Description
ClusterHQ/Flocker provides an efficient and easy way to connect persistent
store with Docker containers. Nexenta's Flocker volume plugin allows the
NexentaEdge data nodes to be moved to a new server when the application’s
Docker container and associated disks are moved. NexentaEdge is a next
generation scale out solution providing block (iSCSI and Cinder) and
object (Swift and S3) storage services.  For more information on NexentaEdge,
see https://nexenta.com/products/nexentaedge. 

##Installation
Make sure that flocker node service has been installed
(For example, to install flocker node service version 1.8.0, see Ubuntu section
 in https://docs.clusterhq.com/en/1.8.0/install/install-node.html for reference)

Install NexentaEdge storage plugin with the following command:
>/opt/flocker/bin/python2.7 setup.py install

##Testing
<pre>
Create a configuration file: /etc/flocker/nedge.yml.
Example:
nedge:
    "cluster_id": "cltest"
    "tenant_id": "test"
    "bucket_id": "ccowbd"
    "chunk_sz": 4096
</pre>

To run the tests, enter-
>trial tests.nedge_tests</br>
    or</br>
>/opt/flocker/bin/trial tests.nedge_tests</br>
(trial is a python program that runs unit-tests. You must in
 working-directory/nedge-flocker-driver directory.)

##Usage
<pre>
Add the following section to the file '/etc/flocker/agent.yml':
"dataset":
    "backend": "nedge_flocker_plugin"
    "cluster_id": "cltest"
    "tenant_id": "test"
    "bucket-id": "ccowbd"
    "chunk_sz": 4096
(This is an example. Use your own values)
</pre>

##Note
The cluster_id, tenant_id and bucket_id must exist, before running the test
or flocker
