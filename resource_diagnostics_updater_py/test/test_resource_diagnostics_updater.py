from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

import rclpy
from diagnostic_msgs.msg import DiagnosticStatus
from rclpy.node import Node

from resource_monitor_interfaces.msg import Field, Resource

from resource_diagnostics_updater_py.diagnosed_resource import DiagnosedResource
from resource_diagnostics_updater_py.diagnostics_publisher import DiagnosticsPublisher
from resource_diagnostics_updater_py.resource_diagnostics_updater import ResourceDiagnosticsUpdater


@pytest.fixture
def test_diagnostics_publisher():
    rclpy.init()
    test_node = Node('test_node')

    diagnostics_publisher_manager = MagicMock()
    diagnostics_publisher_manager.node = test_node

    yield diagnostics_publisher_manager

    test_node.destroy_node()
    rclpy.shutdown()


@dataclass
class UpdaterConfigTestParams:
    diagnosed_resource: DiagnosedResource
    resource_msg: Resource
    expected_diagnostic_status: bytes


@pytest.mark.parametrize(
    'test_parameters',
    [
        pytest.param(
            UpdaterConfigTestParams(
                diagnosed_resource=DiagnosedResource(
                    topic='cpu/cpu_total',
                    name='CPU Usage Active',
                    field='usage_active',
                    warning_threshold=60.0,
                    error_threshold=90.0,
                ),
                resource_msg=Resource(
                    fields=[Field(name='usage_active', value=45.0)],
                ),
                expected_diagnostic_status=DiagnosticStatus.OK,
            ),
            id='cpu and disk resources',
        ),
        pytest.param(
            UpdaterConfigTestParams(
                diagnosed_resource=DiagnosedResource(
                    topic='disk/sda1',
                    name='Disk Usage Free',
                    field='usage_free',
                    warning_threshold=10.0,
                    error_threshold=20.0,
                ),
                resource_msg=Resource(
                    fields=[Field(name='usage_free', value=15.0)],
                ),
                expected_diagnostic_status=DiagnosticStatus.WARN,
            ),
            id='disk usage free warning',
        ),
        pytest.param(
            UpdaterConfigTestParams(
                diagnosed_resource=DiagnosedResource(
                    topic='memory/ram',
                    name='Memory Usage Active',
                    field='usage_active',
                    warning_threshold=70.0,
                    error_threshold=90.0,
                ),
                resource_msg=Resource(
                    fields=[Field(name='usage_active', value=95.0)],
                ),
                expected_diagnostic_status=DiagnosticStatus.ERROR,
            ),
            id='memory usage active error',
        ),
    ],
)
def test_resource_diagnostics_updater_config_loading(
    test_diagnostics_publisher: DiagnosticsPublisher,
    test_parameters: UpdaterConfigTestParams,
):
    diagnostic_updater = ResourceDiagnosticsUpdater(
        test_diagnostics_publisher,
        test_parameters.diagnosed_resource,
        reentrant_callback_group=MagicMock(),
    )

    diagnostic_updater.resource_callback(test_parameters.resource_msg)

    assert diagnostic_updater.diagnostic_status.level == test_parameters.expected_diagnostic_status
