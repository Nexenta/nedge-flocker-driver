#Copyright Nexenta Systems, Inc.

import os
import socket
import functools

from twisted.trial.unittest import SynchronousTestCase, SkipTest
from flocker.node.agents.test.test_blockdevice import make_iblockdeviceapi_tests
from flocker.testtools import skip_except
from nedge_test_main import nedge_test

def nedge_bdapi_test(test_case):
    nbdapi = nedge_test(test_case)
    return nbdapi

@skip_except(
    supported_tests=[
        'test_interface',
        'test_list_volume_empty',
        'test_listed_volume_attributes',
        'test_created_is_listed',
        'test_created_volume_attributes',
        'test_destroy_unknown_volume',
        'test_destroy_volume',
        'test_destroy_destroyed_volume',
        'test_attach_unknown_volume',
        'test_attach_attached_volume',
        'test_attach_elsewhere_attached_volume',
        'test_attach_unattached_volume',
        'test_attached_volume_listed',
        'test_attach_volume_validate_size',
        'test_multiple_volumes_attached_to_host',
        'test_detach_unknown_volume',
        'test_detach_detached_volume',
        'test_reattach_detached_volume',
        'test_attach_destroyed_volume',
        'test_list_attached_and_unattached',
        'test_compute_instance_id_nonempty',
        'test_compute_instance_id_unicode',
        'test_resize_volume_listed',
        'test_resize_unknown_volume',
        'test_resize_destroyed_volume',
        'test_get_device_path_device',
        'test_get_device_path_unknown_volume',
        'test_get_device_path_unattached_volume',
        'test_detach_volume',
        'test_get_device_path_device_repeatable_results',
        'test_device_size'
    ]
)

class NedgeBlockDeviceAPIInterfaceTests(
    make_iblockdeviceapi_tests(
        blockdevice_api_factory=functools.partial(nedge_bdapi_test),
        minimum_allocatable_size=int(1024*1024*1024),
        device_allocation_unit=None,
        unknown_blockdevice_id_factory=lambda test: u'cltest/test/ccowbd/0'
    )
):
    """
    Interface Impl
    """
