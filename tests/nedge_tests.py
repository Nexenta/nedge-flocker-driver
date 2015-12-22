# Copyright Nexenta Systems, Inc.

from flocker.node.agents.test.test_blockdevice import (
    make_iblockdeviceapi_tests)
from nedge_test_main import nedge_test


def nedge_bdapi_test(test_case):
    nbdapi = nedge_test(test_case)
    return nbdapi


class NedgeBlockDeviceAPIInterfaceTests(
    make_iblockdeviceapi_tests(
        nedge_bdapi_test,
        minimum_allocatable_size=int(1024*1024*1024),
        device_allocation_unit=None,
        unknown_blockdevice_id_factory=lambda test: u'cltest/test/ccowbd/0'
    )
):
    """
    Interface Impl
    """
