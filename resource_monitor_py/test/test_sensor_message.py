from dataclasses import dataclass

import pytest

import rclpy
from rclpy.node import Node

from resource_monitor_py.sensor_message import SensorMessage, SensorMessageBuffer


@pytest.fixture
def test_sensor_message_buffer():
    rclpy.init()
    test_node = Node('test_sensor_message_node')

    yield SensorMessageBuffer(test_node.get_logger(), max_buffer_size=100)

    rclpy.shutdown()


@dataclass
class ProcessorTestParams:
    message: str
    expected_message: SensorMessage


@pytest.mark.parametrize(
    'test_parameters',
    [
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"usage_active":9.615384615386088,'
                '"usage_system":1.923076923076739,'
                '"usage_user":4.807692307693044},'
                '"name":"cpu",'
                '"tags":{"cpu":"cpu0"},'
                '"timestamp":1756666979}',
                expected_message=SensorMessage(
                    name='cpu',
                    tags={'cpu': 'cpu0'},
                    fields={
                        'usage_active': 9.615384615386088,
                        'usage_system': 1.923076923076739,
                        'usage_user': 4.807692307693044,
                    },
                    timestamp=1756666979,
                ),
            ),
            id='cpu_cpu0',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"usage_active":7.9999999999936335,'
                '"usage_system":3.0000000000004547,'
                '"usage_user":1.9999999999998295},'
                '"name":"cpu",'
                '"tags":{"cpu":"cpu1"},'
                '"timestamp":1756666979}',
                expected_message=SensorMessage(
                    name='cpu',
                    tags={'cpu': 'cpu1'},
                    fields={
                        'usage_active': 7.9999999999936335,
                        'usage_system': 3.0000000000004547,
                        'usage_user': 1.9999999999998295,
                    },
                    timestamp=1756666979,
                ),
            ),
            id='cpu_cpu1',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"usage_active":6.39097744360071,'
                '"usage_system":2.5062656641607517,'
                '"usage_user":2.8822055137848466},'
                '"name":"cpu",'
                '"tags":{"cpu":"cpu-total"},'
                '"timestamp":1756666979}',
                expected_message=SensorMessage(
                    name='cpu',
                    tags={'cpu': 'cpu-total'},
                    fields={
                        'usage_active': 6.39097744360071,
                        'usage_system': 2.5062656641607517,
                        'usage_user': 2.8822055137848466,
                    },
                    timestamp=1756666979,
                ),
            ),
            id='cpu_cpu_total',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"free":118260555776,'
                '"total":403028406272,'
                '"used_percent":69.08064515956306},'
                '"name":"disk",'
                '"tags":{"path":"root"},'
                '"timestamp":1756666980}',
                expected_message=SensorMessage(
                    name='disk',
                    tags={'path': 'root'},
                    fields={
                        'free': 118260555776,
                        'total': 403028406272,
                        'used_percent': 69.08064515956306,
                    },
                    timestamp=1756666980,
                ),
            ),
            id='disk_root',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"available":8746057728,'
                '"total":16096911360,'
                '"used_percent":43.281958110999994},'
                '"name":"mem",'
                '"tags":{},'
                '"timestamp":1756666980}',
                expected_message=SensorMessage(
                    name='mem',
                    tags={},
                    fields={
                        'available': 8746057728,
                        'total': 16096911360,
                        'used_percent': 43.281958110999994,
                    },
                    timestamp=1756666980,
                ),
            ),
            id='mem_no_tags',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"in_input":0.699},'
                '"name":"sensors",'
                '"tags":{"chip":"amdgpu-pci-0400","feature":"vddgfx"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'amdgpu-pci-0400', 'feature': 'vddgfx'},
                    fields={
                        'in_input': 0.699,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_amdgpu_vddgfx',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"in_input":0.724},'
                '"name":"sensors",'
                '"tags":{"chip":"amdgpu-pci-0400","feature":"vddnb"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'amdgpu-pci-0400', 'feature': 'vddnb'},
                    fields={
                        'in_input': 0.724,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_amdgpu_vddnb',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"temp_input":43},'
                '"name":"sensors",'
                '"tags":{"chip":"amdgpu-pci-0400","feature":"edge"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'amdgpu-pci-0400', 'feature': 'edge'},
                    fields={
                        'temp_input': 43,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_amdgpu_edge',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"power_average":0},'
                '"name":"sensors",'
                '"tags":{"chip":"amdgpu-pci-0400","feature":"slowppt"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'amdgpu-pci-0400', 'feature': 'slowppt'},
                    fields={
                        'power_average': 0,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_amdgpu_slowppt',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"temp_input":44.75},'
                '"name":"sensors",'
                '"tags":{"chip":"k10temp-pci-00c3","feature":"tctl"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'k10temp-pci-00c3', 'feature': 'tctl'},
                    fields={
                        'temp_input': 44.75,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_k10temp_tctl',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"in_input":11.763},'
                '"name":"sensors",'
                '"tags":{"chip":"BAT1-acpi-0","feature":"in0"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'BAT1-acpi-0', 'feature': 'in0'},
                    fields={
                        'in_input': 11.763,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_battery_in0',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"temp_input":36},'
                '"name":"sensors",'
                '"tags":{"chip":"iwlwifi_1-virtual-0","feature":"temp1"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'iwlwifi_1-virtual-0', 'feature': 'temp1'},
                    fields={
                        'temp_input': 36,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_iwlwifi_temp1',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"temp_alarm":0,'
                '"temp_crit":84.85,'
                '"temp_input":31.85,'
                '"temp_max":81.85,'
                '"temp_min":-273.15},'
                '"name":"sensors",'
                '"tags":{"chip":"nvme-pci-0100","feature":"composite"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'nvme-pci-0100', 'feature': 'composite'},
                    fields={
                        'temp_alarm': 0,
                        'temp_crit': 84.85,
                        'temp_input': 31.85,
                        'temp_max': 81.85,
                        'temp_min': -273.15,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_nvme_composite',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"temp_input":31.85,'
                '"temp_max":65261.85,'
                '"temp_min":-273.15},'
                '"name":"sensors",'
                '"tags":{"chip":"nvme-pci-0100","feature":"sensor_1"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'nvme-pci-0100', 'feature': 'sensor_1'},
                    fields={
                        'temp_input': 31.85,
                        'temp_max': 65261.85,
                        'temp_min': -273.15,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_nvme_sensor_1',
        ),
        pytest.param(
            ProcessorTestParams(
                message='{"fields":'
                '{"temp_crit":125,'
                '"temp_input":45},'
                '"name":"sensors",'
                '"tags":{"chip":"acpitz-acpi-0","feature":"temp1"},'
                '"timestamp":1756666978}',
                expected_message=SensorMessage(
                    name='sensors',
                    tags={'chip': 'acpitz-acpi-0', 'feature': 'temp1'},
                    fields={
                        'temp_crit': 125,
                        'temp_input': 45,
                    },
                    timestamp=1756666978,
                ),
            ),
            id='sensors_acpitz_temp1',
        ),
    ],
)
def test_buffer(
    test_sensor_message_buffer: SensorMessageBuffer,
    test_parameters: ProcessorTestParams,
):
    test_sensor_message_buffer.add_message(test_parameters.message)

    assert not test_sensor_message_buffer.is_empty()

    message = test_sensor_message_buffer.get_message()

    assert message is not None
    assert message == test_parameters.expected_message

    assert test_sensor_message_buffer.is_empty()


def test_buffer_drops_oldest_message_when_full(test_sensor_message_buffer: SensorMessageBuffer):
    for timestamp in range(test_sensor_message_buffer.max_buffer_size + 1):
        test_sensor_message_buffer.add_message(
            f'{{"name":"cpu","tags":{{}},"fields":{{}},"timestamp":{timestamp}}}'
        )

    assert len(test_sensor_message_buffer.buffer) == test_sensor_message_buffer.max_buffer_size

    message = test_sensor_message_buffer.get_message()

    assert message is not None
    assert message.timestamp == 1


def test_buffer_drops_malformed_message(test_sensor_message_buffer: SensorMessageBuffer):
    test_sensor_message_buffer.add_message('not json')
    # valid json, but missing the fields a SensorMessage needs
    test_sensor_message_buffer.add_message('{"name":"cpu"}')

    assert test_sensor_message_buffer.get_message() is None
    assert test_sensor_message_buffer.get_message() is None
    assert test_sensor_message_buffer.is_empty()
